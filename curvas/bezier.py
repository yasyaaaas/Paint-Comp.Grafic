"""
Curva de Bézier - implementação baseada no algoritmo de De Casteljau.

Referência:
  Gist "Draw Bezier curves using Python and PyQt" - Alquimista/bezdrae.py
  (https://gist.github.com/1274149/ca37e497b3f2a16c9d3ec4889ed63c80986e9dba)
"""

import math

def binomial(n: int, k: int) -> int:
    """
    Coeficiente binomial C(n,k) = n! / (k! · (n-k)!).
    """
    return math.factorial(n) // (math.factorial(k) * math.factorial(n - k))


def bernstein(t: float, i: int, n: int) -> float:
    """
    Polinômio de Bernstein de grau n, i-ésimo termo, avaliado em t.

    B_i,n(t) = C(n,i) · t^i · (1-t)^(n-i)
    """
    return binomial(n, i) * (t ** i) * ((1 - t) ** (n - i))


def bezier(t: float, pontos: list) -> tuple:
    """
    Calcula as coordenadas (x, y) de um ponto da curva de Bézier
    no parâmetro t, a partir da lista de pontos de controle.

    Fórmula: B(t) = Σ B_i,n(t) · P_i
    """
    n = len(pontos) - 1
    x, y = 0.0, 0.0
    for i, (px, py) in enumerate(pontos):
        b = bernstein(t, i, n)
        x += px * b
        y += py * b
    return int(round(x)), int(round(y))


def pontos_bezier(pontos_controle: list, num_passos: int = 100) -> list:
    """
    Gera uma lista de pontos discretos que aproximam a curva de Bézier.

    Quanto maior num_passos, mais suave é a curva.
    """
    if len(pontos_controle) < 2:
        return []

    resultado = []
    for i in range(num_passos):
        t = i / (num_passos - 1)
        resultado.append(bezier(t, pontos_controle))
    return resultado


class CurvaBezier:
    """
    Renderizador de curvas de Bézier que utiliza um callback para rasterizar
    segmentos de reta entre os pontos calculados.
    """

    def __init__(self, rasterizar_reta_callback):
        """
        rasterizar_reta_callback: função que desenha uma reta entre dois pontos
                                  (x1, y1) e (x2, y2).
        """
        self._rasterizar = rasterizar_reta_callback

    def desenhar(self, pontos_controle: list, num_passos: int = 100) -> None:
        """
        Rasteriza a curva de Bézier definida pelos pontos de controle,
        conectando os pontos calculados com segmentos de reta.
        """
        if len(pontos_controle) < 2:
            return

        pts = pontos_bezier(pontos_controle, num_passos)
        for i in range(len(pts) - 1):
            x1, y1 = pts[i]
            x2, y2 = pts[i + 1]
            self._rasterizar(x1, y1, x2, y2)