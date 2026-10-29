"""
Jogo da Cesta

setas: movem a cesta
enter: iviciar/reiniciar
P: pausa
V: liga/desliga vsync
ESC: fechar tela ok

"""
import sys
from pathlib import Path

import glfw
import moderngl
import numpy as np

SHADERS = Path ( __file__ ) . parent / "shaders"

ROSA = (0.85, 0.10, 0.70, 1.0)
MARROM = (0.60, 0.45, 0.05, 1.0)
VERMELHO = (0.80, 0.05, 0.10, 1.0)
VERDE = (0.15, 0.55, 0.20, 1.0)
ESCALA_CEREJA = 0.05
ESCALA_CESTA = 0.25
LADO = 800 


# Unidades de NDC por SEGUNDO -- nao por quadro . Essa e a diferença do capitulo .
VEL_CEREJA = 0.5 
LIMITE_X = [-0.75, 0.75] 
DT_MAXIMO = 0.05
FUNDO = (0.73, 0.85, 0.92, 1.0)

cesta_x, cesta_y= 0.0, -0.9

#inicializacao
def erro_glfw ( codigo , descricao ) :
    """ Sem este callback , a razao real de uma falha do GLFW e descartada e
    so resta a mensagem generica do sys . exit ."""
    print ( f" GLFW [{ codigo }]: { descricao }", file = sys . stderr )


glfw . set_error_callback ( erro_glfw ) # antes de glfw . init () , de proposito

if not glfw . init () :
    sys . exit (" FALHA : glfw nao inicializou ")

glfw . window_hint ( glfw . CONTEXT_VERSION_MAJOR , 4)
glfw . window_hint ( glfw . CONTEXT_VERSION_MINOR , 0)
glfw . window_hint ( glfw . OPENGL_PROFILE , glfw . OPENGL_CORE_PROFILE )
glfw . window_hint ( glfw . OPENGL_FORWARD_COMPAT , glfw . TRUE )
# Sem a dica acima , o macOS recusa qualquer contexto 3.2+ e
# create_window devolve None . E inofensiva no Windows e no Linux .
glfw . window_hint ( glfw . SAMPLES , 4)
# Sem esta linha , redimensionar a janela deforma a cena : o viewport continua
# com o tamanho antigo , e o NDC deixa de ser quadrado na tela .
glfw . window_hint ( glfw . RESIZABLE , False )

janela = glfw.create_window ( LADO , LADO , "Jogo da Cesta", None , None)
if not janela:
    glfw.terminate ()
    sys.exit (" FALHA : nao foi possivel criar a janela ")

glfw . make_context_current ( janela )
glfw . swap_interval (1) # espera o retraco vertical : ver a nota sobre vsync
ctx = moderngl.create_context ()

prog = ctx . program (
    vertex_shader =(SHADERS/"cesta.vert") . read_text (encoding ="utf-8") ,
    fragment_shader =(SHADERS/"basico.frag"). read_text ( encoding ="utf-8") ,
)



#def's
def ajustar(nome, valor):
    """Escreve num uniforme, se ele existir.

    Um uniforme que o shader deixa de usar e descartado pelo ligador do
    GLSL, e prog[nome] levantaria KeyError. Os experimentos do capitulo
    fazem exatamente isso -- ignorar u_cor, ignorar u_atenuacao -- entao
    o acesso passa todo por aqui.
    """
    uniforme = prog.get(nome, None)
    if uniforme is not None:
        uniforme.value = valor

def leque(x, y):
    """Empacota uma curva fechada como TRIANGLE_FAN: primeiro o centro, depois
    a curva, e o primeiro ponto repetido no fim para fechar a volta."""
    x = np.concatenate(([0.0], x, [x[0]]))
    y = np.concatenate(([0.0], y, [y[0]]))
    return np.column_stack((x, y, np.zeros_like(x), np.ones_like(x))).astype('f4')

def montar(vertices):
    vbo = ctx.buffer(vertices.tobytes())
    return vbo, ctx.vertex_array(prog, [(vbo, '4f', 'vPosition')])

def curva_circulo(n=48):
    t = np.linspace(0.0, 2.0 * np.pi, n, endpoint=False)
    return leque(np.cos(t), np.sin(t))

def desenhar(vao, escala, deslocamento, cor, primitiva):
    """Carrega os tres uniformes daquele desenho e dispara a chamada."""
    ajustar('u_escala', escala)
    ajustar('u_deslocamento', deslocamento)
    ajustar('u_cor', cor)
    vao.render(primitiva)

def desenhar_cesta():
    return np.array([(-0.6, 0.2, 0.0, 1.0), ( 0.6, 0.2, 0.0, 1.0), (-0.4, -0.2, 0.0, 1.0),
                     ( 0.6, 0.2, 0.0, 1.0), ( 0.4, -0.2, 0.0, 1.0), (-0.4, -0.2, 0.0, 1.0),
                     (-0.8, 0.4, 0.0, 1.0), (-0.8, 0.2, 0.0, 1.0), ( 0.8, 0.20, 0.0, 1.0),
                     ( 0.8, 0.2, 0.0, 1.0), ( 0.8, 0.4, 0.0, 1.0), (-0.8, 0.4, 0.0, 1.0)],
                     dtype='f4')

def desenhar_caule():
    return np.array([(-0.15, -0.1, 0.0, 1.0), ( 0.15, -0.1, 0.0, 1.0), ( 0.15, 1.0, 0.0, 1.0),
                     ( 0.15,  1.0, 0.0, 1.0), (-0.15,  1.0, 0.0, 1.0), (-0.15, -0.1, 0.0, 1.0)],
                     dtype='f4')

def desenhar_cereja(x, y):
    desenhar(vao_caule,   ESCALA_CEREJA, (x, y + 0.05), VERDE, moderngl.TRIANGLES)
    desenhar(vao_circulo, ESCALA_CEREJA, (x, y), VERMELHO, moderngl.TRIANGLE_FAN)

def colidiu(cx, cy):
    meia_larg = 0.8 * ESCALA_CESTA + ESCALA_CEREJA                  # 0.20 + 0.05 = 0.25
    meia_alt  = 0.3 * ESCALA_CESTA + ESCALA_CEREJA                  # 0.075 + 0.05 = 0.125
    centro_y  = cesta_y + 0.1 * ESCALA_CESTA                        # -0.9 + 0.025 = -0.875
    return abs(cx - cesta_x) < meia_larg and abs(cy - centro_y) < meia_alt

vbo_cesta, vao_cesta = montar(desenhar_cesta())
vbo_circulo, vao_circulo = montar(curva_circulo())
vbo_caule, vao_caule = montar(desenhar_caule())

def tecla ( window , key , scancode , action , mods ) :
    global cesta_x
    if key == glfw . KEY_ESCAPE and action == glfw . PRESS :
        glfw . set_window_should_close ( window , True )
    elif key in (glfw.KEY_LEFT, glfw.KEY_RIGHT):
        dx = {glfw.KEY_LEFT: -1.0, glfw.KEY_RIGHT: 1.0}.get(key, 0.0)
        cesta_x += dx * DT_MAXIMO
        cesta_x = max(LIMITE_X[0], min(LIMITE_X[1], cesta_x))
    

glfw.set_key_callback (janela, tecla )


#laco principal
instante_anterior = glfw.get_time ()
quadros , marco = 0 , instante_anterior
cerejas = [[-0.6, 1.1], [-0.2, 1.6], [0.2, 2.1], [0.6, 2.6]]
pegas, perdidas = 0, 0

while not glfw . window_should_close ( janela ) :
    agora = glfw.get_time ()  
    dt = min ( agora - instante_anterior , DT_MAXIMO )
    instante_anterior = agora

    for c in cerejas:
        c[1] -= VEL_CEREJA * dt

    # --- desenho ---
    ctx.clear(*FUNDO)
    desenhar(vao_cesta, ESCALA_CESTA, (cesta_x, cesta_y), MARROM, moderngl.TRIANGLES)
    for x, y in cerejas:
        desenhar_cereja(x, y)
    

    glfw . swap_buffers ( janela )
    glfw . poll_events ()

for recurso in (vbo_cesta, vao_cesta, vbo_circulo, vao_circulo, vbo_caule, vao_caule, prog) :
    recurso.release ()
glfw.terminate ()
print ( f" Execucao finalizada")
