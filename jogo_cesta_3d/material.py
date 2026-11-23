"""Materiais e luzes do modelo de Blinn-Phong.

Os coeficientes estao em luz linear: a codificacao sRGB da saida
e feita pelo OpenGL (GL_FRAMEBUFFER_SRGB).
"""
import glm


class Material:
    def __init__(self, nome, ka, kd, ks, alfa):
        self.nome = nome
        self.ka, self.kd, self.ks = glm.vec3(*ka), glm.vec3(*kd), \
            glm.vec3(*ks)
        self.alfa = alfa


# Cada cor e a que se quer ver na tela (sRGB), decodificada uma vez,
# aqui, pela equacao do sRGB.
CEREJA = Material("cereja (plastico vermelho)", (0.250, 0.002, 0.005),
                  (0.711, 0.007, 0.013), (0.600, 0.450, 0.450), 64.0)
CAULE = Material("caule (borracha verde)", (0.014, 0.104, 0.018),
                 (0.040, 0.296, 0.051), (0.030, 0.030, 0.030), 8.0)

# Materiais dos objetos texturizados: a imagem faz o papel de kd (o kd
# daqui nao e lido). Com textura, ka multiplica a cor da imagem, e o
# ambiente de um objeto texturizado tem a cor da sua imagem.
# Valores escolhidos direto em luz linear.
CESTA = Material("cesta (palha)", (0.35, 0.35, 0.35), (1.0, 1.0, 1.0),
                 (0.10, 0.10, 0.10), 20.0)
PISO = Material("piso (tijolo)", (0.35, 0.35, 0.35), (1.0, 1.0, 1.0),
                (0.04, 0.04, 0.04), 8.0)

# Sem iluminacao (a lampada e as sombras): so o kd, como cor pura.
SOMBRA = Material("sombra", (0.0, 0.0, 0.0), (0.0, 0.0, 0.0),
                  (0.0, 0.0, 0.0), 1.0)


class Luz:
    def __init__(self, posicao, id, is_, atenuacao=(1.0, 0.0, 0.0)):
        # w = 1: pontual; w = 0: direcional (posicao e a direcao para a luz)
        self.posicao = glm.vec4(*posicao)
        self.id = glm.vec3(*id)
        self.is_ = glm.vec3(*is_)
        # 1 / (kc + kl d + kq d^2), so para a pontual
        self.atenuacao = glm.vec3(*atenuacao)
        self.ativa = True
