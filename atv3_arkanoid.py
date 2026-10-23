"""
Arkanoid

setas: movem o retanglo
enter: iviciar/reiniciar
espaço: lança a bola
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

LADO = 800 

JOGADOR_Y , ESCALA_JOGADOR = -0.80 , 0.20


# Unidades de NDC por SEGUNDO -- nao por quadro . Essa e a diferença do capitulo .
VEL_JOGADOR , VEL_ALVO , VEL_TIRO = 1.5 , 1.2 , 2.5
LIMITE_Y = [-0.9, 0.9]  # limite do retangulo
DT_MAXIMO = 0.05

FUNDO = (0.02 , 0.03 , 0.23 , 1.0)

# Raquete (y = JOGADOR_Y; limite em x = LIMITE_Y, acima)
RAQUETE_MEIA_LARGURA, RAQUETE_MEIA_ALTURA = 0.15, 0.02
PASSO_RAQUETE = 0.05
COR_RAQUETE = (0.90, 0.90, 0.95, 1.0)

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

janela = glfw . create_window ( LADO , LADO , "Arkanoid", None , None)
if not janela :
    glfw . terminate ()
    sys . exit (" FALHA : nao foi possivel criar a janela ")

glfw . make_context_current ( janela )
glfw . swap_interval (1) # espera o retraco vertical : ver a nota sobre vsync
ctx = moderngl . create_context ()

prog = ctx . program (
    vertex_shader =(SHADERS/"arkanoid.vert") . read_text (encoding ="utf-8") ,
    fragment_shader =(SHADERS/"basico.frag"). read_text ( encoding ="utf-8") ,
)


#def's
def tecla ( window , key , scancode , action , mods ) :
    global atirando
    global raquete_x
    if key == glfw . KEY_ESCAPE and action == glfw . PRESS :
        glfw . set_window_should_close ( window , True )
    elif key in (glfw.KEY_LEFT, glfw.KEY_RIGHT) and action in (glfw.PRESS, glfw.REPEAT):
        dx = {glfw.KEY_LEFT: -1.0, glfw.KEY_RIGHT: 1.0}.get(key, 0.0)
        raquete_x += dx * PASSO_RAQUETE
        raquete_x = max(LIMITE_Y[0] + RAQUETE_MEIA_LARGURA,
                        min(LIMITE_Y[1] - RAQUETE_MEIA_LARGURA, raquete_x))

glfw . set_key_callback ( janela , tecla )


def montar(vertices):
    vbo = ctx.buffer(vertices.tobytes())
    return vbo, ctx.vertex_array(prog, [(vbo, '4f', 'vPosition')])


def ajustar(nome, valor):
    """Escreve num uniforme, se ele existir."""
    uniforme = prog.get(nome, None)
    if uniforme is not None:
        uniforme.value = valor


def desenhar(vao, escala, deslocamento, cor, primitiva):
    """Carrega os tres uniformes daquele desenho e dispara a chamada."""
    ajustar('u_escala', escala)
    ajustar('u_deslocamento', deslocamento)
    ajustar('u_cor', cor)
    vao.render(primitiva)


def retangulo():
    # centrado na origem, ja no tamanho da raquete
    w, h = RAQUETE_MEIA_LARGURA, RAQUETE_MEIA_ALTURA
    return np.array([(-w, -h, 0.0, 1.0), ( w, -h, 0.0, 1.0), ( w,  h, 0.0, 1.0),
                     ( w,  h, 0.0, 1.0), (-w,  h, 0.0, 1.0), (-w, -h, 0.0, 1.0)],
                    dtype='f4')


vbo_retangulo, vao_retangulo = montar(retangulo())


#laco principal
raquete_x = 0.0
instante_anterior = glfw.get_time ()
quadros , marco = 0 , instante_anterior

while not glfw . window_should_close ( janela ) :
    agora = glfw.get_time ()  

    # --- desenho ---
    ctx.clear(*FUNDO)
    desenhar(vao_retangulo, 1.0, (raquete_x, JOGADOR_Y), COR_RAQUETE, moderngl.TRIANGLES)

    glfw . swap_buffers ( janela )
    glfw . poll_events ()

for recurso in (prog ) :
    recurso.release ()
glfw.terminate ()
print ( f" Execucao finalizada")
