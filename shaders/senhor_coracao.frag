#version 400 core
// Usado por 06_senhor_coracao.py e por 09_senhor_coracao_animado.py.

in vec4 v2fcolor;
uniform float u_atenuacao;  // 1.0 de dia, menor a noite
out vec4 outfragcolor;

void main() {
    // .rgb atenua so as tres componentes de cor; .a passa intacto.
    // Atenuar o alfa junto mudaria a opacidade, nao o brilho.
    outfragcolor = vec4(v2fcolor.rgb * u_atenuacao, v2fcolor.a);    
}
