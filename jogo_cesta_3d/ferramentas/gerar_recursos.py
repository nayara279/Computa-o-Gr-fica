"""
Gera os recursos que o jogo usa e que nao vieram da pasta do professor:

  off/cesta.off              cesta de revolucao, com parede, aro e fundo
  off/esfera.off             esfera (a cereja e a lampada)
  texturas/cesta_palha.png   trama de palha, que se repete sem emendas

Os tres sao criados pelo grupo; nao ha modelo nem imagem de terceiros
nesses arquivos. Nao e preciso rodar este script para jogar: os
arquivos gerados ja estao na pasta.

Executar: python ferramentas/gerar_recursos.py
"""
from pathlib import Path

import numpy as np
from PIL import Image

RAIZ = Path(__file__).parent.parent
SEGMENTOS = 48          # divisoes em torno do eixo y


def escrever_off(caminho, vertices, faces):
    linhas = ["OFF", f"{len(vertices)} {len(faces)} 0"]
    linhas += [f"{x:.6f} {y:.6f} {z:.6f}" for x, y, z in vertices]
    linhas += [f"3 {a} {b} {c}" for a, b, c in faces]
    Path(caminho).write_text("\n".join(linhas) + "\n", encoding="utf-8")


def volume_com_sinal(vertices, faces):
    """Positivo quando as faces (anti-horarias) apontam para fora."""
    a, b, c = (vertices[faces[:, i]] for i in range(3))
    return float(np.sum(np.einsum('ij,ij->i', a, np.cross(b, c))) / 6.0)


def revolucao(perfil, n=SEGMENTOS):
    """Gira um perfil fechado (r, y), dado em sentido anti-horario,
    em torno do eixo y. Pontos com r = 0 viram um unico vertice (polo).
    Devolve (vertices, faces) com as faces para fora."""
    vertices, indice = [], {}      # indice[(k, i)]: vertice do ponto k, passo i

    def vertice(k, i):
        r, y = perfil[k]
        chave = (k, 0 if r == 0.0 else i % n)
        if chave not in indice:
            t = 2.0 * np.pi * chave[1] / n
            indice[chave] = len(vertices)
            vertices.append((r * np.cos(t), y, r * np.sin(t)))
        return indice[chave]

    faces = []
    for k in range(len(perfil)):
        k2 = (k + 1) % len(perfil)
        for i in range(n):
            a, b = vertice(k, i), vertice(k, i + 1)
            c, d = vertice(k2, i + 1), vertice(k2, i)
            # (a, b) e a aresta no passo i..i+1; (d, c) a da proxima linha
            for tri in ((a, d, c), (a, c, b)):
                if len(set(tri)) == 3:          # descarta triangulo degenerado
                    faces.append(tri)
    vertices = np.array(vertices, dtype='f8')
    faces = np.array(faces, dtype='u4')
    if volume_com_sinal(vertices, faces) < 0.0:   # inverte, se estiver para dentro
        faces = faces[:, ::-1].copy()
    return vertices, faces


def cesta():
    # (r, y), em sentido anti-horario: fundo externo, parede externa, aro,
    # parede interna e fundo interno. Os pequenos chanfros evitam que a
    # media das normais, nos cantos, borre as arestas.
    perfil = [(0.00, 0.00), (0.50, 0.00), (0.57, 0.04), (0.74, 0.40),
              (0.90, 0.74), (0.92, 0.80), (0.84, 0.84), (0.76, 0.80),
              (0.67, 0.47), (0.58, 0.14), (0.50, 0.08), (0.00, 0.08)]
    return revolucao(perfil)


def esfera(aneis=24, n=SEGMENTOS):
    """Esfera de raio 1, com um vertice em cada polo."""
    vertices = [(0.0, 1.0, 0.0)]
    for j in range(1, aneis):
        phi = np.pi * j / aneis
        for i in range(n):
            t = 2.0 * np.pi * i / n
            vertices.append((np.sin(phi) * np.cos(t), np.cos(phi),
                             np.sin(phi) * np.sin(t)))
    vertices.append((0.0, -1.0, 0.0))
    topo, base = 0, len(vertices) - 1

    def anel(j, i):                       # j de 1 a aneis - 1
        return 1 + (j - 1) * n + i % n

    faces = []
    for i in range(n):
        faces.append((topo, anel(1, i + 1), anel(1, i)))
        faces.append((base, anel(aneis - 1, i), anel(aneis - 1, i + 1)))
    for j in range(1, aneis - 1):
        for i in range(n):
            a, b = anel(j, i), anel(j, i + 1)
            c, d = anel(j + 1, i + 1), anel(j + 1, i)
            faces.append((a, b, c))
            faces.append((a, c, d))
    vertices = np.array(vertices, dtype='f8')
    faces = np.array(faces, dtype='u4')
    if volume_com_sinal(vertices, faces) < 0.0:
        faces = faces[:, ::-1].copy()
    return vertices, faces


def palha(lado=256, celulas=8):
    """Trama de cesto: cada celula e uma tira horizontal ou vertical,
    alternadas como em um tabuleiro. O numero de celulas e par, e a
    imagem se repete sem emendas."""
    rng = np.random.default_rng(7)
    tam = lado // celulas
    y, x = np.mgrid[0:lado, 0:lado]
    ci, cj = y // tam, x // tam
    ty, tx = (y % tam) / tam, (x % tam) / tam
    horizontal = (ci + cj) % 2 == 0
    # dentro da celula, a tira e mais clara no meio e escura nas bordas
    t = np.where(horizontal, ty, tx)
    relevo = np.sin(np.pi * t) ** 0.6
    fibra = np.where(horizontal, x, y) % 5 / 5.0        # fibras finas ao longo da tira
    claro = np.array([0.86, 0.68, 0.38])
    escuro = np.array([0.45, 0.28, 0.12])
    mistura = np.clip(0.25 + 0.70 * relevo - 0.10 * fibra
                      + 0.05 * rng.standard_normal((lado, lado)), 0, 1)
    cor = escuro + (claro - escuro) * mistura[..., None]
    img = (cor * 255).astype('u1')
    return Image.fromarray(img, "RGB")


if __name__ == "__main__":
    for nome, (v, f) in {"cesta": cesta(), "esfera": esfera()}.items():
        escrever_off(RAIZ / "off" / f"{nome}.off", v, f)
        print(f"off/{nome}.off: {len(v)} vertices, {len(f)} faces, "
              f"volume {volume_com_sinal(v, f):.3f}")
    palha().save(RAIZ / "texturas" / "cesta_palha.png")
    print("texturas/cesta_palha.png")
