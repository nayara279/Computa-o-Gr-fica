"""Geometrias geradas por codigo: cilindro, quadrado e disco.

Mesmo formato de Malha.texturada(): 12 floats por vertice, em
posicao (3), normal (3), coordenada de textura (2) e tangente (4).
O jogo nao usa a tangente, mas manter o formato permite que todos
os objetos usem o mesmo vao_de() e o mesmo programa.

As faces saem em sentido anti-horario, vistas de fora, como as da
Malha: com o descarte de faces traseiras ligado, so aparece o lado
de fora.
"""
import numpy as np

TANGENTE = (1.0, 0.0, 0.0, 1.0)      # sem uso: so preenche o formato


def montar(posicoes, normais, uvs, faces):
    n = len(posicoes)
    tangentes = np.tile(np.array(TANGENTE, dtype='f4'), (n, 1))
    dados = np.hstack([np.array(posicoes, dtype='f4'),
                       np.array(normais, dtype='f4'),
                       np.array(uvs, dtype='f4'),
                       tangentes]).astype('f4')
    return dados, np.array(faces, dtype='u4')


def cilindro(n=24):
    """Raio 1, y de 0 a 1, com tampas. Escalado por (r, h, r), vira o
    caule da cereja: uma escala nao uniforme, que a matriz normal
    precisa tratar."""
    pos, nor, uv, faces = [], [], [], []
    # lateral: n + 1 colunas, a ultima repete a primeira (costura de u)
    for i in range(n + 1):
        t = 2.0 * np.pi * i / n
        c, s = np.cos(t), np.sin(t)
        for y in (0.0, 1.0):
            pos.append((c, y, s))
            nor.append((c, 0.0, s))
            uv.append((i / n, y))
    for i in range(n):
        b0, t0, b1, t1 = 2 * i, 2 * i + 1, 2 * i + 2, 2 * i + 3
        faces += [(b0, t1, b1), (b0, t0, t1)]
    # tampas, com vertices proprios: a normal muda de repente na borda
    for y, ny in ((1.0, 1.0), (0.0, -1.0)):
        centro = len(pos)
        pos.append((0.0, y, 0.0))
        nor.append((0.0, ny, 0.0))
        uv.append((0.5, 0.5))
        for i in range(n):
            t = 2.0 * np.pi * i / n
            pos.append((np.cos(t), y, np.sin(t)))
            nor.append((0.0, ny, 0.0))
            uv.append((0.5 + 0.5 * np.cos(t), 0.5 + 0.5 * np.sin(t)))
        for i in range(n):
            a, b = centro + 1 + i, centro + 1 + (i + 1) % n
            faces.append((centro, b, a) if ny > 0 else (centro, a, b))
    return montar(pos, nor, uv, faces)


def quadrado(repeticoes=1.0):
    """Quadrado de lado 2, no plano y = 0, normal para cima. As
    coordenadas de textura vao de 0 a `repeticoes`: com GL_REPEAT, a
    imagem se repete esse numero de vezes em cada direcao."""
    r = repeticoes
    pos = [(-1, 0, -1), (-1, 0, 1), (1, 0, 1), (1, 0, -1)]
    nor = [(0, 1, 0)] * 4
    uv = [(0, 0), (0, r), (r, r), (r, 0)]
    return montar(pos, nor, uv, [(0, 1, 2), (0, 2, 3)])


def disco(n=32):
    """Disco de raio 1, no plano y = 0, normal para cima (as sombras)."""
    pos, nor, uv, faces = [(0.0, 0.0, 0.0)], [(0.0, 1.0, 0.0)], [(0.5, 0.5)], []
    for i in range(n):
        t = 2.0 * np.pi * i / n
        pos.append((np.cos(t), 0.0, np.sin(t)))
        nor.append((0.0, 1.0, 0.0))
        uv.append((0.5 + 0.5 * np.cos(t), 0.5 + 0.5 * np.sin(t)))
    for i in range(n):
        faces.append((0, 1 + (i + 1) % n, 1 + i))
    return montar(pos, nor, uv, faces)
