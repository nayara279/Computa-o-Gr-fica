#version 400 core

in vec3 fDirecao;
uniform samplerCube u_ambiente;
uniform vec3 u_tom;          // o mesmo tom aplicado a cena
out vec4 outfragcolor;

void main() {
    outfragcolor = vec4(texture(u_ambiente, fDirecao).rgb * u_tom, 1.0);
}
