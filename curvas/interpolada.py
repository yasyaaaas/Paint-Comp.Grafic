"""
Curva Interpolada (Catmull-Rom Spline) - passa exatamente por todos os pontos.

Referência:
  Implementação de Catmull-Rom Spline adaptada de:
  Pergunta: https://math.stackexchange.com/questions/1789112/cubic-spline-interpolation-results/1790243
  Código qeu veio em uma resposta com uma implementação da curva interpolada:
  https://math.stackexchange.com/revisions/d6f0ff6b-bf93-4472-a53f-a0cfba902487/view-source
"""

def catmull_rom_ponto(P0, P1, P2, P3, t: float) -> tuple:
    """
    Calcula um ponto da spline Catmull-Rom para o segmento entre P1 e P2,
    utilizando os pontos adjacentes P0 e P3 para definir a tangente.

    Fórmula matricial padrão para Catmull-Rom uniforme (a=0).
    """
    x0, y0 = P0
    x1, y1 = P1
    x2, y2 = P2
    x3, y3 = P3

    t2 = t * t
    t3 = t2 * t

    # Coeficientes da curva cúbica
    cx = 0.5 * ((-x0 + 3*x1 - 3*x2 + x3) * t3 +
                (2*x0 - 5*x1 + 4*x2 - x3) * t2 +
                (-x0 + x2) * t +
                2*x1)
    cy = 0.5 * ((-y0 + 3*y1 - 3*y2 + y3) * t3 +
                (2*y0 - 5*y1 + 4*y2 - y3) * t2 +
                (-y0 + y2) * t +
                2*y1)

    return int(round(cx)), int(round(cy))


def catmull_rom_chain(pontos: list, pontos_por_segmento: int = 20) -> list:
    """
    Gera uma lista de pontos discretos para toda a cadeia de pontos,
    conectando cada par consecutivo com uma spline Catmull-Rom.

    Para os extremos, são criados pontos virtuais que preservam a inclinação
    do primeiro e do último segmento.
    """
    if len(pontos) < 2:
        return []
    if len(pontos) == 2:
        # Apenas uma reta entre os dois pontos
        return [pontos[0], pontos[1]]

    n = len(pontos)
    resultado = []

    for i in range(n - 1):
        # Define os quatro pontos para este segmento
        if i == 0:
            # Primeiro segmento: P0 virtual é uma extrapolação de P0 e P1
            P0 = (2 * pontos[0][0] - pontos[1][0],
                  2 * pontos[0][1] - pontos[1][1])
        else:
            P0 = pontos[i - 1]

        P1 = pontos[i]
        P2 = pontos[i + 1]

        if i == n - 2:
            # Último segmento: P3 virtual é uma extrapolação de Pn-1 e Pn-2
            P3 = (2 * pontos[n - 1][0] - pontos[n - 2][0],
                  2 * pontos[n - 1][1] - pontos[n - 2][1])
        else:
            P3 = pontos[i + 2]

        # Gera pontos para este segmento (exceto o primeiro, para evitar duplicatas)
        for j in range(pontos_por_segmento):
            t = j / pontos_por_segmento
            if i == 0 and j == 0:
                continue  # P1 já foi adicionado na iteração anterior
            resultado.append(catmull_rom_ponto(P0, P1, P2, P3, t))

    return resultado


class CurvaInterpolada:
    """
    Renderizador de curvas interpoladas (Catmull-Rom Spline) que utiliza
    um callback para rasterizar segmentos de reta entre os pontos calculados.
    """

    def __init__(self, rasterizar_reta_callback):
        """
        rasterizar_reta_callback: função que desenha uma reta entre dois pontos
                                  (x1, y1) e (x2, y2).
        """
        self._rasterizar = rasterizar_reta_callback

    def desenhar(self, pontos: list, pontos_por_segmento: int = 30) -> None:
        """
        Rasteriza a curva interpolada (Catmull-Rom) que passa por todos os
        pontos fornecidos, conectando os pontos calculados com segmentos de reta.
        """
        if len(pontos) < 2:
            return

        pts = catmull_rom_chain(pontos, pontos_por_segmento)
        for i in range(len(pts) - 1):
            x1, y1 = pts[i]
            x2, y2 = pts[i + 1]
            self._rasterizar(x1, y1, x2, y2)