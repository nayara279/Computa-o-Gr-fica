#version 400 core

// textura.vert do visualizador, com as repeticoes da textura. Posicao e
// normal vao para o espaco da camera, onde a iluminacao e calculada; a
// coordenada de textura e repassada, e o rasterizador a interpola.

layout(location = 0) in vec4 vPosition;
layout(location = 1) in vec3 vNormal;
layout(location = 2) in vec2 vTexCoord;

uniform mat4 u_modelo, u_visao, u_projecao;
uniform mat3 u_normal;       // inversa transposta de u_modelo
uniform vec2 u_repeticoes;   // repeticoes da imagem em u e em v

out vec3 fP;          // posicao no espaco da camera
out vec3 fN;          // normal no espaco da camera, sem normalizar
out vec2 fTexCoord;

void main() {
    vec4 pos_camera = u_visao * u_modelo * vPosition;
    gl_Position = u_projecao * pos_camera;
    fP = pos_camera.xyz;
    fN = mat3(u_visao) * u_normal * vNormal;
    fTexCoord = vTexCoord * u_repeticoes;
}
