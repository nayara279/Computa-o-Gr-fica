"""Regras do Jogo da Cesta 3D: estado, movimento, colisao e pontuacao.

Nao ha OpenGL aqui. O main.py le o teclado e desenha; este modulo so
decide o que acontece a cada quadro. Os nomes vem do jogo 2D.
"""
import random

import glm

INICIO, JOGANDO, PAUSADO, FIM = (0, 1, 2, 3)

# Unidades do mundo por SEGUNDO -- nao por quadro, como no jogo 2D.
VEL_CEREJA = 1.7
VEL_CESTA = 4.0
LIMITE_X = [-2.5, 2.5]       # ate onde o centro da cesta vai
LIMITE_Z = [-2.5, 2.5]
ALTURA_CEU = 5.0             # y em que a cereja nasce
RAIO_CEREJA = 0.16
META_PEGAS = 20
MAX_PERDIDAS = 5
INTERVALO_CEREJA = 1.4


class Jogo:
    def __init__(self, caixa):
        """caixa: glm.vec3(meia largura em x, altura, meia largura em z) da
        caixa de colisao da cesta, alinhada aos eixos e apoiada no chao."""
        self.caixa = caixa
        self.fase = 0.0          # tempo de jogo: para na pausa
        self.estado = INICIO
        self.reiniciar()

    def reiniciar(self):
        self.cesta = glm.vec3(0.0, 0.0, 0.0)
        self.cerejas = []        # cada uma, [x, y, z]: o centro da esfera
        self.pegas, self.perdidas = 0, 0
        self.tempo_cereja = INTERVALO_CEREJA
        self.venceu = False

    def iniciar(self):
        """ENTER: comeca ou recomeca, sem fechar o programa."""
        self.reiniciar()
        self.estado = JOGANDO

    def alternar_pausa(self):
        if self.estado == JOGANDO:
            self.estado = PAUSADO
        elif self.estado == PAUSADO:
            self.estado = JOGANDO

    def colidiu(self, c):
        """Esfera (a cereja) contra caixa alinhada aos eixos (a cesta): o
        ponto da caixa mais proximo do centro da esfera esta a menos de
        um raio dele."""
        meia_x, altura, meia_z = self.caixa
        px = max(self.cesta.x - meia_x, min(c[0], self.cesta.x + meia_x))
        py = max(0.0, min(c[1], altura))
        pz = max(self.cesta.z - meia_z, min(c[2], self.cesta.z + meia_z))
        dx, dy, dz = c[0] - px, c[1] - py, c[2] - pz
        return dx * dx + dy * dy + dz * dz < RAIO_CEREJA ** 2

    def atualizar(self, dt, sentido_x, sentido_z):
        """dt em segundos; sentido_x e sentido_z, de -1 a 1, vem das setas."""
        if self.estado != PAUSADO:
            self.fase += dt
        if self.estado != JOGANDO:
            return

        # cesta: velocidade em unidades por segundo, igual na diagonal
        sentido = glm.vec2(sentido_x, sentido_z)
        if glm.length(sentido) > 1.0:
            sentido = glm.normalize(sentido)
        self.cesta.x += sentido.x * VEL_CESTA * dt
        self.cesta.z += sentido.y * VEL_CESTA * dt
        self.cesta.x = max(LIMITE_X[0], min(LIMITE_X[1], self.cesta.x))
        self.cesta.z = max(LIMITE_Z[0], min(LIMITE_Z[1], self.cesta.z))

        # nascimento continuo de cerejas
        self.tempo_cereja += dt
        if self.tempo_cereja >= INTERVALO_CEREJA:
            self.tempo_cereja -= INTERVALO_CEREJA
            self.cerejas.append([random.uniform(*LIMITE_X), ALTURA_CEU,
                                 random.uniform(*LIMITE_Z)])

        # queda, colisao e chao
        for c in self.cerejas[:]:
            c[1] -= VEL_CEREJA * dt
            if self.colidiu(c):
                self.pegas += 1
                self.cerejas.remove(c)
            elif c[1] - RAIO_CEREJA < 0.0:      # a esfera tocou o piso
                self.perdidas += 1
                self.cerejas.remove(c)

        # vitoria / derrota
        if self.pegas >= META_PEGAS:
            self.venceu = True
            self.estado = FIM
        elif self.perdidas >= MAX_PERDIDAS:
            self.venceu = False
            self.estado = FIM
