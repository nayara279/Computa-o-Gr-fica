"""Camera LookAt, com dois modos, e a projecao perspectiva.

SEGUE: acompanha a cesta, de tras e de cima.
GERAL: olha a arena inteira de cima; o mouse gira a cena (trackball).

As duas usam glm.lookAt(olho, centro, cima) e a mesma projecao.
"""
import glm

FOVY = 60.0          # abertura vertical, em graus (a do visualizador era 45)

# Como no visualizador, os planos near e far envolvem uma esfera: aqui,
# a que contem a arena inteira (piso, cesta e as cerejas no ceu), com
# centro na origem. O trackball gira a cena em torno da origem, entao a
# esfera nao sai do lugar. near fica o mais longe possivel da camera, o
# que da mais precisao ao teste de profundidade; so cai para NEAR_MIN
# quando o olho esta dentro da esfera.
RAIO_CENA = 9.0
MARGEM = 0.05
NEAR_MIN = 0.1

SEGUE, GERAL = 0, 1
NOMES = ["segue a cesta", "visao geral"]
ELEVACAO = [glm.radians(25.0), glm.radians(35.0)]   # angulo acima do chao
ZOOM = [(5.0, 14.0), (7.0, 20.0)]                   # distancia minima e maxima
CENTRO_GERAL = glm.vec3(0.0, 1.0, 0.0)
FRENTE_SEGUE = glm.vec3(0.0, 1.5, -1.0)   # para onde a camera olha, a partir da cesta


class Camera:
    def __init__(self):
        self.modo = SEGUE
        self.distancias = [8.0, 13.0]       # uma por modo
        self.alvo = glm.vec3(0.0, 0.0, 0.0)  # a posicao da cesta
        self.cima = glm.vec3(0.0, 1.0, 0.0)
        self.aspecto = 1.0
        self.fovy = glm.radians(FOVY)

    @property
    def nome(self):
        return NOMES[self.modo]

    @property
    def distancia(self):
        return self.distancias[self.modo]

    def alternar_modo(self):
        self.modo = 1 - self.modo

    def seguir(self, posicao):
        self.alvo = glm.vec3(posicao)

    def aproximar(self, passo):
        """Roda do mouse: passo > 0 aproxima."""
        minimo, maximo = ZOOM[self.modo]
        self.distancias[self.modo] = float(glm.clamp(
            self.distancia - passo, minimo, maximo))

    @property
    def centro(self):
        if self.modo == SEGUE:
            return self.alvo + FRENTE_SEGUE
        return CENTRO_GERAL

    @property
    def olho(self):
        e = ELEVACAO[self.modo]
        return self.centro + self.distancia * glm.vec3(0.0, glm.sin(e), glm.cos(e))

    @property
    def near(self):
        return max(NEAR_MIN, glm.length(self.olho) - RAIO_CENA - MARGEM)

    @property
    def far(self):
        return glm.length(self.olho) + RAIO_CENA + MARGEM

    def visao(self):
        return glm.lookAt(self.olho, self.centro, self.cima)

    def projecao(self):
        return glm.perspective(self.fovy, self.aspecto, self.near, self.far)
