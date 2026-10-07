"""
Quadrado com variaveis uniformes : a escala e a cor vem do Python .
O 05 _quadrado_diagonal .py sem a cor nos vertices : u_escala muda o
tamanho do quadrado , e u_cor da uma cor a cada triangulo .
MCCC007 -23 - Computacao Grafica - UFABC

Executar : python 05 u_quadrado_uniform .py
Teclas : ESPACO alterna a diagonal | D alterna o fundo | ESC sai
SETA CIMA aumenta o quadrado | SETA BAIXO diminui
"""
import sys
from pathlib import Path

import glfw
import moderngl
import numpy as np

SHADERS = Path ( __file__ ) . parent / "shaders"

VERTICES = np . array ([
    -0.5 , -0.5 , 0.0 , 1.0 ,
    0.5 , -0.5 , 0.0 , 1.0 ,
    0.5 , 0.5 , 0.0 , 1.0 ,
    -0.5 , 0.5 , 0.0 , 1.0 ,
] , dtype ='f4')

# Os mesmos quatro vertices , triangulados de duas maneiras . Muda so a ordem
# de leitura ; o VBO nao e tocado .
DIAGONAL_02 = np . array ([0 , 1 , 2 , 2 , 3 , 0] , dtype ='u4')
DIAGONAL_13 = np . array ([0 , 1 , 3 , 1 , 2 , 3] , dtype ='u4')

BRANCO = (1.0 , 1.0 , 1.0 , 1.0)
PRETO = (0.0 , 0.0 , 0.0 , 1.0)
VERMELHO = (1.0 , 0.0 , 0.0 , 1.0)
AMARELO = (1.0 , 1.0 , 0.0 , 1.0)

# Com lado 1.0 no VBO , escala 2.0 faz o quadrado ocupar a janela inteira .
PASSO_ESCALA = 0.1
ESCALA_MIN = 0.1
ESCALA_MAX = 2.0

def erro_glfw ( codigo , descricao ) :
    """ Sem este callback , a razao real de uma falha do GLFW e descartada ."""
    print ( f" GLFW [{ codigo }]: { descricao }", file = sys . stderr )


glfw . set_error_callback ( erro_glfw ) # antes de glfw . init () , de proposito

if not glfw . init () :
    sys . exit (" FALHA : glfw nao inicializou ")

glfw . window_hint ( glfw . CONTEXT_VERSION_MAJOR , 4)
glfw . window_hint ( glfw . CONTEXT_VERSION_MINOR , 0)
glfw . window_hint ( glfw . OPENGL_PROFILE , glfw . OPENGL_CORE_PROFILE )
glfw . window_hint ( glfw . OPENGL_FORWARD_COMPAT , glfw . TRUE )
# Sem a dica acima , o macOS recusa qualquer contexto 3.2+.

janela = glfw . create_window (600 , 600 , " Uniformes ", None , None )
if not janela :
    glfw . terminate ()
    sys . exit (" FALHA : nao foi possivel criar a janela ")

glfw . make_context_current ( janela )
glfw . swap_interval (1)
ctx = moderngl . create_context ()

prog = ctx . program (
    vertex_shader =( SHADERS / "uniquad.vert") . read_text ( encoding ="utf-8") ,
    fragment_shader =( SHADERS / "basico.frag"). read_text ( encoding ="utf-8") ,
)

vbo = ctx . buffer ( VERTICES . tobytes () )
ebo = ctx . buffer ( DIAGONAL_02 . tobytes () )
vao = ctx . vertex_array (
    prog ,
    [( vbo , '4f', 'vPosition') ] ,
    index_buffer = ebo ,
)

# O estado que os exemplos anteriores nao tinham .
diagonal_alternativa = False
modo_noite = False
escala = 1.0


def tecla ( window , key , scancode , action , mods ) :
    """ Chamada pelo GLFW uma vez por evento de teclado .

    Os argumentos sao fixos , e o estado do programa nao esta entre eles .
    Para altera -lo , a funcao declara as variaveis como global . Sem essa
    declaracao , a atribuicao criaria variaveis locais .

    """
    global diagonal_alternativa , modo_noite , escala
    if action == glfw . RELEASE :
        return

    # As setas aceitam tambem glfw . REPEAT : segurar a tecla continua escalando .
    if key == glfw . KEY_UP :
        escala = min ( escala + PASSO_ESCALA , ESCALA_MAX )
    elif key == glfw . KEY_DOWN :
        escala = max ( escala - PASSO_ESCALA , ESCALA_MIN )

    if action != glfw . PRESS :
        return

    if key == glfw . KEY_ESCAPE :
        glfw . set_window_should_close ( window , True )
    elif key == glfw . KEY_D :
        modo_noite = not modo_noite
    elif key == glfw . KEY_SPACE :
        diagonal_alternativa = not diagonal_alternativa
        # Reescreve os 24 bytes do EBO ja alocado , sem recriar buffer nem VAO .
        novos = DIAGONAL_13 if diagonal_alternativa else DIAGONAL_02
        ebo . write ( novos . tobytes () )


glfw . set_key_callback ( janela , tecla )

while not glfw . window_should_close ( janela ) :
    ctx . clear (*( PRETO if modo_noite else BRANCO ) )
    prog ['u_escala']. value = escala
    # Um uniform vale para a chamada inteira ; para cada triangulo ter sua
    # cor , desenhamos um de cada vez , trocando u_cor entre as chamadas .
    prog ['u_cor']. value = VERMELHO
    vao . render ( moderngl . TRIANGLES , vertices =3 , first =0) # 0 a 2
    prog ['u_cor']. value = AMARELO
    vao . render ( moderngl . TRIANGLES , vertices =3 , first =3) # 3 a 5
    glfw . swap_buffers ( janela )
    glfw . poll_events ()

for recurso in ( vao , ebo , vbo , prog ) :
    recurso . release ()
glfw . terminate ()
print (" Execucao finalizada .")