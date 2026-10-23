"""
Arkanoid

setas: movem a raquete
enter: iniciar/reiniciar
espaco: lanca a bola
P: pausa
V: liga/desliga vsync
ESC: fechar tela

MCCC007-23 - Computacao Grafica - UFABC
Executar: python atv3_arkanoid.py
"""
import sys
from pathlib import Path

import glfw
import glm
import moderngl
import numpy as np

SHADERS = Path(__file__).parent / "shaders"

LADO = 800                      # janela quadrada

# Raquete
RAQUETE_Y = -0.80
RAQUETE_LARGURA, RAQUETE_ALTURA = 0.30, 0.04
COR_RAQUETE = (0.90, 0.90, 0.95, 1.0)

# Unidades de NDC por SEGUNDO -- nao por quadro. Essa e a diferenca do capitulo.
VEL_JOGADOR = 1.5
LIMITE_X = 0.9                  # parede: a BORDA da raquete para aqui
DT_MAXIMO = 0.05                # trava de seguranca contra passo grande

FUNDO = (0.02, 0.03, 0.23, 1.0)

I = glm.mat4(1.0)               # identidade

# ---------------------------------------------------------------- inicializacao


def erro_glfw(codigo, descricao):
    """Sem este callback, a razao real de uma falha do GLFW e descartada e
    so resta a mensagem generica do sys.exit."""
    print(f"GLFW [{codigo}]: {descricao}", file=sys.stderr)


glfw.set_error_callback(erro_glfw)   # antes de glfw.init(), de proposito

if not glfw.init():
    sys.exit("FALHA: glfw nao inicializou")

glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 4)
glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 0)
glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
glfw.window_hint(glfw.OPENGL_FORWARD_COMPAT, glfw.TRUE)
# Sem a dica acima, o macOS recusa qualquer contexto 3.2+ e
# create_window devolve None. E inofensiva no Windows e no Linux.
glfw.window_hint(glfw.SAMPLES, 4)
# Sem esta linha, redimensionar a janela deforma a cena: o viewport continua
# com o tamanho antigo, e o NDC deixa de ser quadrado na tela.
glfw.window_hint(glfw.RESIZABLE, False)

janela = glfw.create_window(LADO, LADO, "Arkanoid", None, None)
if not janela:
    glfw.terminate()
    sys.exit("FALHA: nao foi possivel criar a janela")

glfw.make_context_current(janela)
glfw.swap_interval(1)            # espera o retraco vertical
ctx = moderngl.create_context()

prog = ctx.program(
    vertex_shader=(SHADERS / "arkanoid.vert").read_text(encoding="utf-8"),
    fragment_shader=(SHADERS / "basico.frag").read_text(encoding="utf-8"),
)
u_modelo = prog['u_modelo']
u_cor = prog['u_cor']

# --------------------------------------------------------------------- geometria


def montar(vertices):
    vbo = ctx.buffer(vertices.tobytes())
    return vbo, ctx.vertex_array(prog, [(vbo, '4f', 'vPosition')])


def retangulo():
    """Mesmo retangulo da cena 2D, so com outras coordenadas: 1 x 1 e CENTRADO
    na origem (antes: 0.1 x 1, com a origem na base). O tamanho real vem da
    matriz, e o centro na origem deixa a colisao por meias-larguras direta."""
    return np.array([(-0.5, -0.5, 0.0, 1.0), ( 0.5, -0.5, 0.0, 1.0), ( 0.5,  0.5, 0.0, 1.0),
                     ( 0.5,  0.5, 0.0, 1.0), (-0.5,  0.5, 0.0, 1.0), (-0.5, -0.5, 0.0, 1.0)],
                    dtype='f4')


vbo_retangulo, vao_retangulo = montar(retangulo())     # criado UMA vez


def matriz_modelo(x, y, w, h):
    """Escala (w, h) primeiro, depois desloca para (x, y): le-se da direita
    para a esquerda, como no exemplo de transformacoes."""
    return glm.translate(I, glm.vec3(x, y, 0.0)) * glm.scale(I, glm.vec3(w, h, 1.0))


def desenhar(vao, modelo, cor, primitiva):
    """Carrega os dois uniformes daquele desenho e dispara a chamada."""
    u_modelo.write(modelo.to_bytes())     # to_bytes(): ordem por colunas
    u_cor.value = cor
    vao.render(primitiva)


# ---------------------------------------------------------------------- teclado


def tecla(window, key, scancode, action, mods):
    if key == glfw.KEY_ESCAPE and action == glfw.PRESS:
        glfw.set_window_should_close(window, True)


glfw.set_key_callback(janela, tecla)

# ------------------------------------------------------------------ laco principal

RAQUETE_MEIA = RAQUETE_LARGURA / 2
raquete_x = 0.0

instante_anterior = glfw.get_time()
quadros, marco = 0, instante_anterior

while not glfw.window_should_close(janela):
    agora = glfw.get_time()
    dt = min(agora - instante_anterior, DT_MAXIMO)
    instante_anterior = agora

    # --- atualizacao: tudo multiplicado por dt, nada por quadro ---
    # Movimento continuo: consulta direta do estado das teclas.
    direita = glfw.get_key(janela, glfw.KEY_RIGHT) == glfw.PRESS
    esquerda = glfw.get_key(janela, glfw.KEY_LEFT) == glfw.PRESS
    raquete_x += (float(direita) - float(esquerda)) * VEL_JOGADOR * dt
    # O limite vale para a BORDA, entao o centro para antes: LIMITE_X - meia.
    raquete_x = max(-LIMITE_X + RAQUETE_MEIA, min(LIMITE_X - RAQUETE_MEIA, raquete_x))

    # --- desenho ---
    ctx.clear(*FUNDO)
    desenhar(vao_retangulo,
             matriz_modelo(raquete_x, RAQUETE_Y, RAQUETE_LARGURA, RAQUETE_ALTURA),
             COR_RAQUETE, moderngl.TRIANGLES)

    glfw.swap_buffers(janela)
    glfw.poll_events()

for recurso in (vao_retangulo, vbo_retangulo, prog):
    recurso.release()
glfw.terminate()
print("Execucao finalizada")
