"""
Jogo da Cesta 3D (Atividade 5): continuacao do Jogo da Cesta 2D.

Cerejas caem do ceu e a cesta as apanha. Cada cereja pega vale 1 ponto e
cada cereja que toca o chao custa 1 das 5 vidas. Vence com 20 pegas;
perde ao ficar sem vidas.

Os modulos malha, texturas e trackball sao os do visualizador da apostila
(v3), sem alteracoes; camera e material foram adaptados dele. O laco, o
placar, as regras e os estados vem do jogo 2D (jogo.py e placar.py).
O mapa cubico (texturas/cubemap/) e de Emil Persson (Humus,
http://www.humus.name), licenca CC BY 3.0.

MCCC007-23 - Computacao Grafica - UFABC

Executar: python main.py
Teclas:   SETAS movem a cesta (esquerda/direita e frente/tras)
          ENTER inicia e reinicia | P pausa | V liga/desliga o vsync
          C troca a camera: segue a cesta / visao geral
          L liga/desliga a luz direcional | W aramado
          Z endireita a cena | I inercia | ESC sai
Mouse:    arrastar gira a cena (camera geral) | roda aproxima e afasta
Estados:  inicio, jogando, pausado e fim (vitoria ou derrota)
"""
import sys
from pathlib import Path

import glfw
import glm
import moderngl
import numpy as np

sys.path.insert(0, str(Path(__file__).parent))          # modulos comuns

import camera as cam                                    # noqa: E402
import texturas as tx                                   # noqa: E402
from camera import Camera                               # noqa: E402
from formas import cilindro, disco, quadrado            # noqa: E402
from jogo import (Jogo, INICIO, JOGANDO, PAUSADO, FIM,  # noqa: E402
                  RAIO_CEREJA, ALTURA_CEU, META_PEGAS, MAX_PERDIDAS)
from malha import Malha                                 # noqa: E402
from material import (CEREJA, CAULE, CESTA, PISO, LAMPADA,  # noqa: E402
                      SOMBRA, Luz)
from placar import Placar                               # noqa: E402
from trackball import Trackball                         # noqa: E402

AQUI = Path(__file__).parent
LADO = 800
FUNDO = (0.08, 0.09, 0.11)
DT_MAXIMO = 0.05         # passo maximo: evita saltos ao arrastar a janela
PASSO_ZOOM = 0.5         # variacao da distancia por clique da roda

# Cena, em unidades do mundo (o piso esta em y = 0).
METADE_PISO = 6.0
REPETICOES_PISO = 8.0    # a imagem do piso se repete 8 x 8 (GL_REPEAT)
REPETICOES_CESTA = (4.0, 2.0)   # repeticoes da trama em torno e na altura
ESCALA_CESTA = 0.95      # raio da esfera envolvente da cesta
FATOR_BOCA = 0.62        # a caixa de colisao e a que cabe na boca redonda
FATOR_TOPO = 0.55        # a caixa vai ate essa fracao da altura da cesta
INCLINACAO_CAULE = -20.0   # graus
TAMANHO_CAULE = (0.02, 0.45, 0.02)   # escala NAO uniforme do cilindro
OPACIDADE_SOMBRA = 0.45

# Luzes: a lampada (pontual, com atenuacao) gira em torno da arena; o ceu
# (direcional) e fixo. Ambas, ao mesmo tempo.
AMBIENTE = glm.vec3(0.55, 0.55, 0.62)
RAIO_LAMPADA, ALTURA_LAMPADA, VEL_LAMPADA = 3.4, 2.8, 0.7   # VEL em rad/s
RAIO_ESFERA_LAMPADA = 0.14

# Tom aplicado a cena inteira, no lugar das cores de fundo do jogo 2D.
TOM_NORMAL = glm.vec3(1.0, 1.0, 1.0)
TOM_PAUSA = glm.vec3(0.38, 0.42, 0.72)
TOM_VITORIA = glm.vec3(0.75, 1.00, 0.75)
TOM_DERROTA = glm.vec3(1.00, 0.62, 0.62)

PASTA_TEXTURAS = AQUI / "texturas"
PASTA_OFF = AQUI / "off"
CUBO = "cubemap"

# O moderngl nao tem nome para este estado do OpenGL.
GL_FRAMEBUFFER_SRGB = 0x8DB9

# Os objetos usam os 12 floats de Malha.texturada(): posicao, normal,
# coordenada de textura e tangente (que o jogo nao le).
CAMPOS_TEXTURA = [('3f', 'vPosition'), ('3f', 'vNormal'),
                  ('2f', 'vTexCoord'), ('4f', 'vTangente')]


def erro_glfw(codigo, descricao):
    print(f"GLFW [{codigo}]: {descricao}", file=sys.stderr)


def matriz_normal(modelo):
    """Inversa transposta do bloco 3x3 da matriz de modelo."""
    return glm.transpose(glm.inverse(glm.mat3(modelo)))


def carregar_programa(ctx, nome):
    return ctx.program(
        vertex_shader=(AQUI / "shaders" / f"{nome}.vert")
        .read_text(encoding="utf-8"),
        fragment_shader=(AQUI / "shaders" / f"{nome}.frag")
        .read_text(encoding="utf-8"))


def vao_de(ctx, prog, vbo, ebo=None, campos=CAMPOS_TEXTURA):
    """VAO que liga so os atributos que o programa declara. No
    formato, '4x4' pula quatro valores de 4 bytes."""
    formato, nomes = [], []
    for tamanho, nome in campos:
        if nome in prog:
            formato.append(tamanho)
            nomes.append(nome)
        else:
            formato.append(f"{tamanho[0]}x4")
    return ctx.vertex_array(prog, [(vbo, " ".join(formato), *nomes)],
                            index_buffer=ebo)


def enviar(prog, **uniformes):
    """Envia os uniformes que o programa declara e ignora os outros,
    como vao_de faz com os atributos."""
    for nome, valor in uniformes.items():
        if nome not in prog:
            continue
        if isinstance(valor, (glm.mat3, glm.mat4)):
            prog[nome].write(valor.to_bytes())    # por colunas
        else:
            prog[nome].value = valor


def abrir(nome):
    caminho = PASTA_TEXTURAS / nome
    if not caminho.exists():
        sys.exit(f"FALHA: imagem nao encontrada: {caminho}")
    return tx.ler(caminho)


class Album:
    """As texturas do programa, lidas no inicio, uma so vez. As de cor
    ficam em GL_SRGB8_ALPHA8, com mipmaps, filtro trilinear e GL_REPEAT
    (texturas.carregar)."""

    def __init__(self, ctx):
        print("lendo texturas...", flush=True)
        self.piso = tx.carregar(ctx, abrir("brick_base.jpg"), srgb=True)
        self.cesta = tx.carregar(ctx, abrir("cesta_palha.png"), srgb=True)
        pasta_cubo = PASTA_TEXTURAS / CUBO
        if not pasta_cubo.is_dir():
            sys.exit(f"FALHA: pasta nao encontrada: {pasta_cubo}")
        self.cubo = tx.carregar_cubo(ctx, pasta_cubo)

    def liberar(self):
        for tex in (self.piso, self.cesta, self.cubo):
            tex.release()


class Objeto:
    """Uma geometria, criada uma unica vez: VBO, EBO e VAO. Cada vez que
    e desenhada, a matriz de modelo vem de fora, por uniforme."""

    def __init__(self, ctx, prog, dados, indices, enquadramento=None):
        self.vbo = ctx.buffer(dados.tobytes())
        self.ebo = ctx.buffer(indices.tobytes())
        self.vao = vao_de(ctx, prog, self.vbo, self.ebo)
        # Malhas lidas de arquivo: a matriz que as leva para a esfera de
        # raio F na origem. As coordenadas do arquivo nao sao alteradas.
        self.enquadramento = enquadramento if enquadramento is not None \
            else glm.mat4(1.0)

    def desenhar(self):
        self.vao.render(moderngl.TRIANGLES)

    def liberar(self):
        for recurso in (self.vao, self.vbo, self.ebo):
            recurso.release()


def cubo_do_skybox(ctx, prog):
    """Doze triangulos, so posicao; cada posicao e uma direcao."""
    c = np.array([[-1, -1, -1], [1, -1, -1], [1, 1, -1], [-1, 1, -1],
                  [-1, -1, 1], [1, -1, 1], [1, 1, 1], [-1, 1, 1]],
                 dtype='f4')
    faces = [(0, 1, 2), (2, 3, 0), (4, 5, 6), (6, 7, 4), (0, 4, 7),
             (7, 3, 0), (1, 5, 6), (6, 2, 1), (3, 2, 6), (6, 7, 3),
             (0, 1, 5), (5, 4, 0)]
    vbo = ctx.buffer(c[np.array(faces).ravel()].tobytes())
    return ctx.vertex_array(prog, [(vbo, '3f', 'vPosition')]), vbo


def tom_do_estado(jogo):
    if jogo.estado == PAUSADO:
        return TOM_PAUSA
    if jogo.estado == FIM:
        return TOM_VITORIA if jogo.venceu else TOM_DERROTA
    return TOM_NORMAL


def desenhar_quadro(ctx, prog, objetos, album, skybox, placar, estado,
                    camera, bola, jogo, lampada, ceu):
    # O fundo ja e uma cor de tela: limpa sem codificar.
    ctx.disable_direct(GL_FRAMEBUFFER_SRGB)
    ctx.clear(*FUNDO, depth=1.0)
    ctx.enable_direct(GL_FRAMEBUFFER_SRGB)

    # Teste de profundidade e descarte de faces traseiras sempre ligados.
    ctx.enable(moderngl.DEPTH_TEST)
    ctx.enable(moderngl.CULL_FACE)
    ctx.wireframe = estado["aramado"]

    # No modo geral, o trackball gira o mundo inteiro (objetos, luzes e
    # ceu) em torno da origem; a visao continua sendo um LookAt.
    mundo = bola.matriz() if camera.modo == cam.GERAL else glm.mat4(1.0)
    visao = camera.visao()
    projecao = camera.projecao()
    tom = tom_do_estado(jogo)
    I = glm.mat4(1.0)

    # Luzes no espaco da camera, o mesmo dos pontos e das normais.
    sem_luz = glm.vec3(0.0)
    enviar(prog,
           u_visao=visao, u_projecao=projecao, u_ia=AMBIENTE,
           u_luz_p=visao * mundo * lampada.posicao,
           u_id_p=lampada.id, u_is_p=lampada.is_,
           u_atenuacao=lampada.atenuacao,
           u_luz_d=visao * mundo * ceu.posicao,
           u_id_d=ceu.id if ceu.ativa else sem_luz,
           u_is_d=ceu.is_ if ceu.ativa else sem_luz,
           u_tom=tom, u_base=0)

    def desenhar(objeto, modelo, mat, textura=None, repeticoes=(1.0, 1.0),
                 iluminar=True, opacidade=1.0):
        enviar(prog, u_modelo=modelo, u_normal=matriz_normal(modelo),
               u_ka=mat.ka, u_kd=mat.kd, u_ks=mat.ks, u_alfa=mat.alfa,
               u_textura=textura is not None, u_iluminar=iluminar,
               u_opacidade=opacidade, u_repeticoes=repeticoes)
        if textura is not None:
            textura.use(0)
        objeto.desenhar()

    # piso: o mesmo quadrado, escalado por (6, 1, 6)
    desenhar(objetos["piso"],
             mundo * glm.scale(I, glm.vec3(METADE_PISO, 1.0, METADE_PISO)),
             PISO, album.piso)

    # sombras das cerejas: discos escuros no piso, que crescem na descida
    ctx.enable(moderngl.BLEND)
    for x, y, z in jogo.cerejas:
        r = RAIO_CEREJA * (0.5 + 1.0 * (1.0 - min(1.0, y / ALTURA_CEU)))
        desenhar(objetos["disco"],
                 mundo * glm.translate(I, glm.vec3(x, 0.012, z))
                 * glm.scale(I, glm.vec3(r, 1.0, r)),
                 SOMBRA, iluminar=False, opacidade=OPACIDADE_SOMBRA)
    ctx.disable(moderngl.BLEND)

    # cesta: lida de off/cesta.off, enquadrada e apoiada no piso
    cesta = objetos["cesta"]
    desenhar(cesta,
             mundo * glm.translate(I, glm.vec3(jogo.cesta.x, objetos["base"],
                                               jogo.cesta.z))
             * cesta.enquadramento,
             CESTA, album.cesta, repeticoes=REPETICOES_CESTA)

    # cerejas: a esfera de off/esfera.off e o caule, um cilindro fino
    esfera = objetos["esfera"]
    for x, y, z in jogo.cerejas:
        desenhar(esfera,
                 mundo * glm.translate(I, glm.vec3(x, y, z))
                 * glm.scale(I, glm.vec3(RAIO_CEREJA)) * esfera.enquadramento,
                 CEREJA)
        desenhar(objetos["caule"],
                 mundo * glm.translate(I, glm.vec3(x, y + 0.9 * RAIO_CEREJA, z))
                 * glm.rotate(I, glm.radians(INCLINACAO_CAULE),
                              glm.vec3(0.0, 0.0, 1.0))
                 * glm.scale(I, glm.vec3(*TAMANHO_CAULE)),
                 CAULE)

    # ceu: o skybox, por ultimo, no plano far
    ctx.wireframe = False
    vao, prog_sky = skybox
    visao_rot = glm.mat4(glm.mat3(visao * mundo))   # sem a translacao
    enviar(prog_sky, u_visao_rot=visao_rot, u_projecao=projecao,
           u_ambiente=0, u_tom=tom)
    album.cubo.use(0)
    ctx.disable(moderngl.CULL_FACE)           # a camera esta dentro
    # O skybox tem profundidade 1, o valor da limpeza: o teste
    # precisa aceitar a igualdade.
    ctx.depth_func = '<='
    vao.render(moderngl.TRIANGLES)
    ctx.depth_func = '<'

    # segunda passada, o placar: ortografica, sem teste de profundidade,
    # com as cores como estao (sem codificacao sRGB).
    ctx.disable(moderngl.DEPTH_TEST)
    ctx.disable_direct(GL_FRAMEBUFFER_SRGB)
    placar.desenhar(jogo, camera.aspecto)
    ctx.enable(moderngl.DEPTH_TEST)


def titulo(jogo, camera, estado, ceu, fps):
    nome = {INICIO: "ENTER para iniciar", JOGANDO: "Jogando",
            PAUSADO: "PAUSADO",
            FIM: "VITORIA! (ENTER reinicia)" if jogo.venceu
            else "DERROTA (ENTER reinicia)"}[jogo.estado]
    return (f"Jogo da Cesta 3D - {nome} - pegas {jogo.pegas}/{META_PEGAS}"
            f" - perdidas {jogo.perdidas}/{MAX_PERDIDAS}"
            f" - camera: {camera.nome}"
            f" - luz direcional {'ligada' if ceu.ativa else 'desligada'}"
            f" - vsync {'ligado' if estado['vsync'] else 'DESLIGADO'}"
            + (" - ARAMADO" if estado["aramado"] else "")
            + f" - {fps:5.1f} fps")


def main():
    glfw.set_error_callback(erro_glfw)
    if not glfw.init():
        sys.exit("FALHA: glfw nao inicializou")

    glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 4)
    glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 0)
    glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
    glfw.window_hint(glfw.OPENGL_FORWARD_COMPAT, glfw.TRUE)  # macOS
    glfw.window_hint(glfw.SAMPLES, 4)
    glfw.window_hint(glfw.SRGB_CAPABLE, True)

    janela = glfw.create_window(LADO, LADO, "Jogo da Cesta 3D", None, None)
    if not janela:
        glfw.terminate()
        sys.exit("FALHA: nao foi possivel criar a janela")

    glfw.make_context_current(janela)
    glfw.swap_interval(1)            # espera o retraco vertical
    ctx = moderngl.create_context()
    ctx.enable(moderngl.DEPTH_TEST)

    prog = carregar_programa(ctx, "jogo")
    prog_skybox = carregar_programa(ctx, "skybox")
    album = Album(ctx)
    vao_skybox, vbo_skybox = cubo_do_skybox(ctx, prog_skybox)
    skybox = (vao_skybox, prog_skybox)
    placar = Placar(ctx, AQUI / "shaders")

    # Geometrias, todas criadas aqui, uma unica vez.
    malha_cesta = Malha(PASTA_OFF / "cesta.off")
    malha_esfera = Malha(PASTA_OFF / "esfera.off")
    print(malha_cesta.resumo())
    print(malha_esfera.resumo())
    objetos = {
        # lidas de arquivo OFF; a coordenada de textura vem do mapeamento
        # cilindrico (cesta) e esferico (esfera), com a costura corrigida
        "cesta": Objeto(ctx, prog, *malha_cesta.texturada("cilindrico", "y"),
                        malha_cesta.matriz_enquadramento(ESCALA_CESTA)),
        "esfera": Objeto(ctx, prog, *malha_esfera.texturada("esferico", "y"),
                         malha_esfera.matriz_enquadramento(1.0)),
        # geradas por codigo (formas.py)
        "caule": Objeto(ctx, prog, *cilindro()),
        "piso": Objeto(ctx, prog, *quadrado(REPETICOES_PISO)),
        "disco": Objeto(ctx, prog, *disco()),
    }

    # A cesta tem o fundo no piso: o enquadramento a deixa centrada na
    # origem, e `base` a levanta. A caixa de colisao sai das medidas da
    # malha, ja na escala do mundo.
    escala = ESCALA_CESTA / malha_cesta.raio
    minimo = malha_cesta.vertices.min(axis=0)
    maximo = malha_cesta.vertices.max(axis=0)
    objetos["base"] = float((malha_cesta.centro[1] - minimo[1]) * escala)
    altura = float((maximo[1] - minimo[1]) * escala)
    caixa = glm.vec3(FATOR_BOCA * float(maximo[0] - minimo[0]) * escala / 2.0,
                     FATOR_TOPO * altura,
                     FATOR_BOCA * float(maximo[2] - minimo[2]) * escala / 2.0)

    jogo = Jogo(caixa)
    camera = Camera()
    bola = Trackball()
    lampada = Luz((RAIO_LAMPADA, ALTURA_LAMPADA, 0.0, 1.0),
                  id=(1.0, 0.85, 0.60), is_=(1.0, 1.0, 1.0),
                  atenuacao=(1.0, 0.05, 0.02))
    ceu = Luz((-0.4, 1.0, 0.6, 0.0), id=(0.55, 0.58, 0.70),
              is_=(0.35, 0.35, 0.40))
    estado = {"aramado": False, "vsync": True}

    def tecla(window, key, scancode, action, mods):
        # acoes discretas, por callback; o movimento continuo e lido no laco
        if action != glfw.PRESS:
            return
        if key == glfw.KEY_ESCAPE:
            glfw.set_window_should_close(window, True)
        elif key == glfw.KEY_ENTER:
            jogo.iniciar()
        elif key == glfw.KEY_P:
            jogo.alternar_pausa()
        elif key == glfw.KEY_V:
            estado["vsync"] = not estado["vsync"]
            glfw.swap_interval(1 if estado["vsync"] else 0)
        elif key == glfw.KEY_C:
            camera.alternar_modo()
        elif key == glfw.KEY_L:
            ceu.ativa = not ceu.ativa
        elif key == glfw.KEY_W:
            estado["aramado"] = not estado["aramado"]
        elif key == glfw.KEY_I:
            bola.inercia = not bola.inercia
            bola.velocidade = 0.0
        elif key == glfw.KEY_Z:
            bola.zerar()

    def botao(window, button, action, mods):
        if button != glfw.MOUSE_BUTTON_LEFT:
            return
        x, y = glfw.get_cursor_pos(window)
        if action == glfw.PRESS and camera.modo == cam.GERAL:
            bola.pressionar(x, y)
        elif action == glfw.RELEASE:
            bola.soltar()

    def roda(window, dx, dy):
        camera.aproximar(dy * PASSO_ZOOM)

    def redimensionou(window, largura, altura):
        largura, altura = max(1, largura), max(1, altura)
        ctx.viewport = (0, 0, largura, altura)
        camera.aspecto = largura / altura
        lj, aj = glfw.get_window_size(window)
        bola.redimensionar(max(1, lj), max(1, aj))

    glfw.set_key_callback(janela, tecla)
    glfw.set_mouse_button_callback(janela, botao)
    glfw.set_scroll_callback(janela, roda)
    glfw.set_framebuffer_size_callback(janela, redimensionou)
    redimensionou(janela, *glfw.get_framebuffer_size(janela))

    print("\nSETAS movem a cesta | ENTER inicia/reinicia | P pausa")
    print("V vsync | C camera | L luz direcional | W aramado | ESC sai")
    print("mouse: arrastar gira a cena (camera geral) | roda aproxima")

    instante_anterior = glfw.get_time()
    quadros, marco = 0, instante_anterior

    while not glfw.window_should_close(janela):
        agora = glfw.get_time()
        dt = min(agora - instante_anterior, DT_MAXIMO)
        instante_anterior = agora          # a pausa nao acumula tempo

        # --- atualizacao: tudo multiplicado por dt, nada por quadro ---
        # Movimento continuo: consulta direta do estado das teclas.
        esquerda = glfw.get_key(janela, glfw.KEY_LEFT) == glfw.PRESS
        direita = glfw.get_key(janela, glfw.KEY_RIGHT) == glfw.PRESS
        frente = glfw.get_key(janela, glfw.KEY_UP) == glfw.PRESS
        tras = glfw.get_key(janela, glfw.KEY_DOWN) == glfw.PRESS
        jogo.atualizar(dt, float(direita) - float(esquerda),
                       float(tras) - float(frente))
        camera.seguir(jogo.cesta)

        # A lampada gira com o tempo de jogo, que para na pausa.
        angulo = VEL_LAMPADA * jogo.fase
        lampada.posicao = glm.vec4(RAIO_LAMPADA * glm.cos(angulo),
                                   ALTURA_LAMPADA,
                                   RAIO_LAMPADA * glm.sin(angulo), 1.0)

        if bola.arrastando:
            bola.mover(*glfw.get_cursor_pos(janela), dt)
        elif jogo.estado != PAUSADO:
            bola.atualizar(dt)

        desenhar_quadro(ctx, prog, objetos, album, skybox, placar, estado,
                        camera, bola, jogo, lampada, ceu)

        glfw.swap_buffers(janela)
        glfw.poll_events()

        # --- titulo: estado, placar e fps ---
        quadros += 1
        if agora - marco >= 0.5:
            fps = quadros / (agora - marco)
            glfw.set_window_title(janela, titulo(jogo, camera, estado, ceu, fps))
            quadros, marco = 0, agora

    for nome, objeto in objetos.items():
        if isinstance(objeto, Objeto):
            objeto.liberar()
    album.liberar()
    placar.liberar()
    vao_skybox.release()
    vbo_skybox.release()
    prog_skybox.release()
    prog.release()
    glfw.terminate()
    print("Execucao finalizada.")


if __name__ == "__main__":
    main()
