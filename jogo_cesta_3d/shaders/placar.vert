#version 400 core

// O vertex shader do jogo 2D, com a projecao ortografica do placar.

layout(location = 0) in vec4 vPosition;

uniform mat4  u_projecao;      // ortografica: (-aspecto, aspecto) x (-1, 1)
uniform float u_escala;
uniform vec2  u_deslocamento;
uniform vec4  u_cor;

out vec4 v2fcolor;

void main() {
    gl_Position = u_projecao * vec4(vPosition.xy * u_escala + u_deslocamento,
                                    vPosition.zw);
    v2fcolor = u_cor;
}
