"""Placar do jogo, desenhado com geometria em uma segunda passada sobre a
cena 3D: projecao ortografica e teste de profundidade desligado.

As funcoes leque, curva_circulo, curva_coracao, montar, ajustar e desenhar
sao as do jogo 2D e da cena 2D (Senhor Coracao), com a projecao a mais.
As coordenadas vao de -aspecto a aspecto em x e de -1 a 1 em y.
"""
from pathlib import Path

import glm
import moderngl
import numpy as np

from jogo import INICIO, PAUSADO, FIM, META_PEGAS, MAX_PERDIDAS

VERMELHO = (0.80, 0.05, 0.10, 1.0)
VERDE = (0.20, 0.65, 0.25, 1.0)
AMARELO = (1.0, 0.90, 0.0, 1.0)
BRANCO = (1.0, 1.0, 1.0, 1.0)
MAGENTA = (0.85, 0.10, 0.45, 1.0)
VINHO = (0.55, 0.05, 0.08, 1.0)

ESCALA_VIDA = 0.04
VIDAS_CANTO = (0.10, 0.90)      # distancia da borda esquerda e do topo
VIDAS_PASSO = 0.11
PULSO_FREQ = 0.8                # pulsacoes por segundo
PULSO_AMPL = 0.2

ESCALA_MARCA = 0.026            # uma marca por cereja pega
MARCAS_POR_LINHA = 10
MARCAS_PASSO = 0.07
MARCAS_CANTO = (0.10, 0.93)     # distancia da borda direita e do topo


def leque(x, y):
    """Empacota uma curva fechada como TRIANGLE_FAN: primeiro o centro, depois
    a curva, e o primeiro ponto repetido no fim para fechar a volta."""
    x = np.concatenate(([0.0], x, [x[0]]))
    y = np.concatenate(([0.0], y, [y[0]]))
    return np.column_stack((x, y, np.zeros_like(x), np.ones_like(x))).astype('f4')


def curva_coracao(n=180):
    t = np.linspace(0.0, 2.0 * np.pi, n, endpoint=False)
    x = 16.0 * np.sin(t) ** 3
    y = (13.0 * np.cos(t) - 5.0 * np.cos(2 * t)
         - 2.0 * np.cos(3 * t) - np.cos(4 * t))
    y = y - 0.5 * (y.max() + y.min())      # centra a curva na origem
    return leque(x / 17.0, y / 17.0)       # normaliza para caber em [-1, 1]


def curva_circulo(n=48):
    t = np.linspace(0.0, 2.0 * np.pi, n, endpoint=False)
    return leque(np.cos(t), np.sin(t))


def poligono(pontos):
    return np.array([(x, y, 0.0, 1.0) for x, y in pontos], dtype='f4')


def retangulo(x0, y0, x1, y1):
    """Dois triangulos."""
    return poligono([(x0, y0), (x1, y0), (x1, y1),
                     (x1, y1), (x0, y1), (x0, y0)])


class Placar:
    def __init__(self, ctx, pasta_shaders):
        self.ctx = ctx
        self.prog = ctx.program(
            vertex_shader=(Path(pasta_shaders) / "placar.vert")
            .read_text(encoding="utf-8"),
            fragment_shader=(Path(pasta_shaders) / "placar.frag")
            .read_text(encoding="utf-8"))

        # Todas as geometrias, criadas uma so vez. As posicoes, o tamanho e
        # a cor de cada desenho vao por uniforme.
        formas = {
            "circulo": curva_circulo(),                         # TRIANGLE_FAN
            "coracao": curva_coracao(),                         # TRIANGLE_FAN
            "caule": retangulo(-0.15, -0.1, 0.15, 1.0),         # TRIANGLES
            "marca": retangulo(-1.0, -1.0, 1.0, 1.0),           # TRIANGLES
            "contorno": poligono([(-1, -1), (1, -1), (1, 1), (-1, 1)]),  # LINE_LOOP
            "play": poligono([(-0.6, -0.8), (0.9, 0.0), (-0.6, 0.8)]),   # TRIANGLES
            "barra": retangulo(-0.3, -1.0, 0.3, 1.0),           # TRIANGLES
            # o X da derrota: duas tiras diagonais
            "xis": np.vstack([
                poligono([(-1.0, -0.8), (-0.8, -1.0), (1.0, 0.8),
                          (1.0, 0.8), (0.8, 1.0), (-1.0, -0.8)]),
                poligono([(-1.0, 0.8), (-0.8, 1.0), (1.0, -0.8),
                          (1.0, -0.8), (0.8, -1.0), (-1.0, 0.8)])]),
        }
        self.vbos, self.vaos = {}, {}
        for nome, vertices in formas.items():
            self.vbos[nome] = ctx.buffer(vertices.tobytes())
            self.vaos[nome] = ctx.vertex_array(
                self.prog, [(self.vbos[nome], '4f', 'vPosition')])

    def ajustar(self, nome, valor):
        """Escreve num uniforme, se ele existir."""
        uniforme = self.prog.get(nome, None)
        if uniforme is not None:
            uniforme.value = valor

    def desenhar_forma(self, nome, escala, deslocamento, cor, primitiva):
        """Carrega os tres uniformes daquele desenho e dispara a chamada."""
        self.ajustar('u_escala', escala)
        self.ajustar('u_deslocamento', deslocamento)
        self.ajustar('u_cor', cor)
        self.vaos[nome].render(primitiva)

    def cereja(self, x, y, escala):
        """A mesma cereja das vidas do jogo 2D: caule e circulo."""
        self.desenhar_forma("caule", escala, (x, y + escala), VERDE,
                            moderngl.TRIANGLES)
        self.desenhar_forma("circulo", escala, (x, y), VERMELHO,
                            moderngl.TRIANGLE_FAN)

    def desenhar(self, jogo, aspecto):
        projecao = glm.ortho(-aspecto, aspecto, -1.0, 1.0, -1.0, 1.0)
        self.prog['u_projecao'].write(projecao.to_bytes())

        # vidas: uma cereja pulsando por vida restante
        for i in range(MAX_PERDIDAS - jogo.perdidas):
            k = 1.0 + PULSO_AMPL * np.sin(
                2.0 * np.pi * PULSO_FREQ * jogo.fase + 0.6 * i)
            self.cereja(-aspecto + VIDAS_CANTO[0] + i * VIDAS_PASSO,
                        VIDAS_CANTO[1] - ESCALA_VIDA, ESCALA_VIDA * k)

        # pontos: um quadrado cheio por cereja pega, dentro do contorno
        # (LINE_LOOP) das que faltam para a meta
        for i in range(META_PEGAS):
            x = aspecto - MARCAS_CANTO[0] \
                - (MARCAS_POR_LINHA - 1 - i % MARCAS_POR_LINHA) * MARCAS_PASSO
            y = MARCAS_CANTO[1] - (i // MARCAS_POR_LINHA) * MARCAS_PASSO
            if i < jogo.pegas:
                self.desenhar_forma("marca", ESCALA_MARCA, (x, y), AMARELO,
                                    moderngl.TRIANGLES)
            self.desenhar_forma("contorno", ESCALA_MARCA, (x, y), BRANCO,
                                moderngl.LINE_LOOP)

        # o estado, no centro
        if jogo.estado == INICIO:
            self.desenhar_forma("play", 0.20, (0.0, 0.0), BRANCO,
                                moderngl.TRIANGLES)
        elif jogo.estado == PAUSADO:
            for lado in (-1.0, 1.0):
                self.desenhar_forma("barra", 0.13, (lado * 0.10, 0.0), BRANCO,
                                    moderngl.TRIANGLES)
        elif jogo.estado == FIM:
            if jogo.venceu:
                self.desenhar_forma("coracao", 0.30, (0.0, 0.0), MAGENTA,
                                    moderngl.TRIANGLE_FAN)
            else:
                self.desenhar_forma("xis", 0.25, (0.0, 0.0), VINHO,
                                    moderngl.TRIANGLES)

    def liberar(self):
        for recurso in list(self.vaos.values()) + list(self.vbos.values()) \
                + [self.prog]:
            recurso.release()
