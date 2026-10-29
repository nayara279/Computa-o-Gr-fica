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

ROSA = (0.85, 0.10, 0.70, 1.00)
MARROM = (0.60, 0.45, 0.05, 1.0)
ESCALA_CESTA = 0.25
LADO = 800 
JOGADOR_Y , ESCALA_JOGADOR = -0.80 , 0.20


# Unidades de NDC por SEGUNDO -- nao por quadro . Essa e a diferença do capitulo .
VEL_JOGADOR , VEL_ALVO , VEL_TIRO = 1.5 , 1.2 , 2.5 
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

def desenhar(vao, escala, deslocamento, cor, primitiva):
    """Carrega os tres uniformes daquele desenho e dispara a chamada."""
    ajustar('u_escala', escala)
    ajustar('u_deslocamento', deslocamento)
    ajustar('u_cor', cor)
    vao.render(primitiva)

def montar(vertices):
    vbo = ctx.buffer(vertices.tobytes())
    return vbo, ctx.vertex_array(prog, [(vbo, '4f', 'vPosition')])

def desenhar_cesta():
    return np.array([(-0.6, 0.2, 0.0, 1.0), ( 0.6, 0.2, 0.0, 1.0), (-0.4, -0.2, 0.0, 1.0),
                     ( 0.6, 0.2, 0.0, 1.0), ( 0.4, -0.2, 0.0, 1.0), (-0.4, -0.2, 0.0, 1.0),
                     (-0.8, 0.4, 0.0, 1.0), (-0.8, 0.2, 0.0, 1.0), ( 0.8, 0.20, 0.0, 1.0),
                     ( 0.8, 0.2, 0.0, 1.0), ( 0.8, 0.4, 0.0, 1.0), (-0.8, 0.4, 0.0, 1.0)],
                     dtype='f4')

vbo_cesta, vao_cesta = montar(desenhar_cesta())

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

while not glfw . window_should_close ( janela ) :
    agora = glfw.get_time ()  

    # --- desenho ---
    ctx.clear(*FUNDO)
    desenhar(vao_cesta, ESCALA_CESTA, (cesta_x, cesta_y), MARROM, moderngl.TRIANGLES)
    
    glfw . swap_buffers ( janela )
    glfw . poll_events ()

for recurso in (vbo_cesta, vao_cesta, prog) :
    recurso.release ()
glfw.terminate ()
print ( f" Execucao finalizada")
