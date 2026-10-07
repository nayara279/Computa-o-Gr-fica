"""
Dois triangulos atravessando a tela: um por quadro, outro por tempo.

MCCC007-23 - Computacao Grafica - UFABC

Executar: python 07_triangulo_animado.py
Teclas:   V liga e desliga o vsync | ESC sai
"""
import sys
from pathlib import Path

import glfw
import moderngl
import numpy as np

SHADERS = Path(__file__).parent / "shaders"

VELOCIDADE = 0.5          # unidades de NDC por SEGUNDO
PASSO = VELOCIDADE / 60.0  # o mesmo avanco, se a maquina fizer 60 quadros/s
PARTIDA, CHEGADA = -0.9, 0.9  # pq a tela vai de -1, 1


def triangulo(r, g, b):
    """Um triangulo apontando para a direita, com a cor no proprio VBO."""
    return np.array([
        [-0.6, -0.7, 0.0, 1.0,  r, g, b, 1.0],
        [ 1.0,  0.0, 0.0, 1.0,  r, g, b, 1.0],
        [-0.6,  0.7, 0.0, 1.0,  r, g, b, 1.0],
    ], dtype='f4')


def erro_glfw(codigo, descricao):
    """Substitui o aviso padrão do pyGLFW: imprime código 
    e descrição de qualquer erro do GLFW em stderr"""
    print(f"GLFW [{codigo}]: {descricao}", file=sys.stderr)


glfw.set_error_callback(erro_glfw)   # antes de glfw.init(), de proposito

if not glfw.init():
    sys.exit("FALHA: glfw nao inicializou")

glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 4)
glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 0)
glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
glfw.window_hint(glfw.OPENGL_FORWARD_COMPAT, glfw.TRUE)

janela = glfw.create_window(900, 400, "Por quadro x por tempo", None, None)
if not janela:
    glfw.terminate()
    sys.exit("FALHA: nao foi possivel criar a janela")

glfw.make_context_current(janela)
glfw.swap_interval(1)    
ctx = moderngl.create_context()

prog = ctx.program(
    vertex_shader=(SHADERS / "acerte_o_alvo.vert").read_text(encoding="utf-8"),
    fragment_shader=(SHADERS / "basico.frag").read_text(encoding="utf-8"),
)

vbo_quadro = ctx.buffer(triangulo(0.95, 0.35, 0.30).tobytes())   
vbo_tempo = ctx.buffer(triangulo(0.30, 0.85, 0.45).tobytes())    
vao_quadro = ctx.vertex_array(prog, [(vbo_quadro, '4f 4f', 'vPosition', 'vColors')])
vao_tempo = ctx.vertex_array(prog, [(vbo_tempo, '4f 4f', 'vPosition', 'vColors')])

vsync = True


def tecla(window, key, scancode, action, mods):
    global vsync
    if action != glfw.PRESS:
        return
    if key == glfw.KEY_ESCAPE:
        glfw.set_window_should_close(window, True)
    elif key == glfw.KEY_V:
        vsync = not vsync
        glfw.swap_interval(1 if vsync else 0)


glfw.set_key_callback(janela, tecla)

x_quadro = x_tempo = PARTIDA
instante_anterior = glfw.get_time()
quadros, marco = 0, instante_anterior

while not glfw.window_should_close(janela):
    agora = glfw.get_time()
    dt = agora - instante_anterior
    instante_anterior = agora

    # As duas linhas que o capitulo compara.
    x_quadro += PASSO
    x_tempo += VELOCIDADE * dt

    if x_quadro > CHEGADA:
        x_quadro = PARTIDA
    if x_tempo > CHEGADA:
        x_tempo = PARTIDA

    ctx.clear(0.10, 0.11, 0.13, 1.0)
    for vao, x, y in ((vao_quadro, x_quadro, 0.4), (vao_tempo, x_tempo, -0.4)):
        prog['u_escala'].value = 0.10
        prog['u_deslocamento'].value = (x, y)
        vao.render(moderngl.TRIANGLES)

    glfw.swap_buffers(janela)
    glfw.poll_events()

    quadros += 1
    if agora - marco >= 0.5:
        glfw.set_window_title(
            janela, f"vsync {'on' if vsync else 'OFF'} - "
                    f"{quadros / (agora - marco):6.1f} fps")
        quadros, marco = 0, agora

for recurso in (vao_quadro, vao_tempo, vbo_quadro, vbo_tempo, prog):
    recurso.release()
glfw.terminate()
print("Execucao finalizada.")