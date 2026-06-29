"""
Curva de Hermite Cúbica - implementação baseada em funções de base de Hermite.

Referência:
  Código adaptado de: https://github.com/vedantyadu/Hermite-cubic-spline
"""

def hermite_ponto(P0, P1, T0, T1, t: float) -> tuple:
    """
    Calcula um ponto da curva de Hermite no parâmetro t ∈ [0,1].
    P0, P1: pontos extremos. T0, T1: vetores tangentes.
    """
    t2 = t * t
    t3 = t2 * t

    # Funções de base de Hermite (Ferguson cubic)
    h1 =  2*t3 - 3*t2 + 1      # h00
    h2 = -2*t3 + 3*t2          # h01
    h3 =   t3 - 2*t2 + t       # h10
    h4 =   t3 - t2             # h11

    x = h1 * P0[0] + h2 * P1[0] + h3 * T0[0] + h4 * T1[0]
    y = h1 * P0[1] + h2 * P1[1] + h3 * T0[1] + h4 * T1[1]
    return int(round(x)), int(round(y))


def pontos_hermite(pontos_controle: list, num_passos: int = 100) -> list:
    """
    Gera uma lista de pontos discretos para a curva Hermite.
    Espera 4 pontos: [P0, R0, R1, P1] onde T0 = R0 - P0 e T1 = P1 - R1.
    """
    if len(pontos_controle) != 4:
        return pontos_controle  # fallback

    P0, R0, R1, P1 = pontos_controle
    T0 = (R0[0] - P0[0], R0[1] - P0[1])
    T1 = (P1[0] - R1[0], P1[1] - R1[1])

    pts = []
    for i in range(num_passos):
        t = i / (num_passos - 1)
        pts.append(hermite_ponto(P0, P1, T0, T1, t))
    return pts


class CurvaHermite:
    """
    Renderizador de curvas de Hermite que utiliza um callback para rasterizar
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
        Rasteriza a curva Hermite definida por 4 pontos de controle,
        conectando os pontos calculados com segmentos de reta.
        """
        if len(pontos_controle) != 4:
            return

        pts = pontos_hermite(pontos_controle, num_passos)
        for i in range(len(pts) - 1):
            x1, y1 = pts[i]
            x2, y2 = pts[i + 1]
            self._rasterizar(x1, y1, x2, y2)