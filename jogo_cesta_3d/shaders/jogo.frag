#version 400 core

// Sombreamento de Phong: a equacao de Blinn-Phong e avaliada uma vez por
// fragmento, com a posicao e a normal interpoladas, para duas fontes: uma
// pontual com atenuacao (a lampada, que se move) e uma direcional (o ceu).
// Todos os pontos e vetores estao no espaco da camera. A saida e luz
// linear; o OpenGL a codifica em sRGB (GL_FRAMEBUFFER_SRGB).

in vec3 fP;
in vec3 fN;
in vec2 fTexCoord;

uniform sampler2D u_base;    // albedo, GL_SRGB8_ALPHA8: chega em luz linear
uniform bool  u_textura;     // true: a imagem faz o papel de kd
uniform bool  u_iluminar;    // false: cor pura (a lampada e as sombras)
uniform vec3  u_ka, u_kd, u_ks;
uniform float u_alfa;
uniform vec3  u_ia;          // luz ambiente

uniform vec4  u_luz_p;       // pontual: posicao, w = 1
uniform vec3  u_id_p, u_is_p;
uniform vec3  u_atenuacao;   // kc, kl, kq
uniform vec4  u_luz_d;       // direcional: direcao para a luz, w = 0
uniform vec3  u_id_d, u_is_d;

uniform vec3  u_tom;         // multiplica a cor final (pausa, vitoria, derrota)
uniform float u_opacidade;

out vec4 outfragcolor;

// Parcelas difusa e especular de uma fonte. A mesma funcao serve as
// duas: o w de luz escolhe entre pontual e direcional, como em phong.frag.
vec3 fonte(vec4 luz, vec3 id, vec3 is, vec3 kd, vec3 P, vec3 N) {
    vec3 L = (luz.w == 1.0) ? normalize(luz.xyz - P)    // pontual
                            : normalize(luz.xyz);       // direcional
    vec3 V = normalize(-P);                             // camera na origem
    float NdotL = max(dot(N, L), 0.0);

    // sem brilho especular onde a luz nao chega
    float brilho = 0.0;
    if (NdotL > 0.0) {
        vec3 H = normalize(L + V);
        brilho = pow(max(dot(N, H), 0.0), u_alfa);
    }

    float atenuacao = 1.0;
    if (luz.w == 1.0) {
        float d = length(luz.xyz - P);
        atenuacao = 1.0 / (u_atenuacao.x + u_atenuacao.y * d
                           + u_atenuacao.z * d * d);
    }
    return atenuacao * (kd * id * NdotL + u_ks * is * brilho);
}

void main() {
    if (!u_iluminar) {
        outfragcolor = vec4(u_kd * u_tom, u_opacidade);
        return;
    }

    vec3 N = normalize(fN);    // a interpolacao encurta a normal
    vec3 kd = u_kd;
    vec3 ambiente = u_ka * u_ia;
    if (u_textura) {
        kd = texture(u_base, fTexCoord).rgb;      // a cor da imagem no lugar de kd
        ambiente = u_ka * u_ia * kd;
    }

    vec3 cor = ambiente
             + fonte(u_luz_p, u_id_p, u_is_p, kd, fP, N)
             + fonte(u_luz_d, u_id_d, u_is_d, kd, fP, N);
    outfragcolor = vec4(cor * u_tom, u_opacidade);
}
