"""
Algoritmos de recorte de segmentos de reta.

Ambos os algoritmos recebem uma Reta e os limites da janela de recorte,
e retornam uma nova Reta com os extremos ajustados para os limites da janela,
ou None se o segmento estiver completamente fora.
O objeto Reta original nunca é modificado.
"""

from typing import Optional
from .formas import Ponto, Reta


class AlgoritmosRecorte:

    @staticmethod
    def cohen_sutherland(reta: Reta, xmin: float, ymin: float,
                         xmax: float, ymax: float) -> Optional[Reta]:
        """
        Algoritmo de Cohen-Sutherland.

        Atribui a cada ponto um código de 4 bits indicando em qual região
        fora da janela ele está. Com base nos códigos dos dois extremos:
          - ambos zero -> segmento completamente dentro -> aceita
          - AND != 0   -> ambos do mesmo lado de fora   -> rejeita
          - caso geral -> recorta o ponto externo contra a borda do bit ativo
            e repete, até cair em um dos dois casos acima.
        """

        def calcular_codigo(x: float, y: float) -> int:
            # Cada bit representa uma região fora da janela:
            # bit 0 (1) = esquerda, bit 1 (2) = direita
            # bit 2 (4) = abaixo,   bit 3 (8) = acima
            # (Y cresce para baixo na tela, então ymin é o topo e ymax é a base)
            codigo = 0
            if x < xmin:
                codigo |= 1  # ESQUERDA
            elif x > xmax:
                codigo |= 2  # DIREITA
            if y < ymin:
                codigo |= 4  # SUPERIOR (topo da tela)
            elif y > ymax:
                codigo |= 8  # INFERIOR (base da tela)
            return codigo

        x1, y1 = reta.p1.x, reta.p1.y
        x2, y2 = reta.p2.x, reta.p2.y
        codigo1 = calcular_codigo(x1, y1)
        codigo2 = calcular_codigo(x2, y2)
        aceito = False

        while True:
            if codigo1 == 0 and codigo2 == 0:
                # Ambos os pontos dentro da janela: aceita diretamente
                aceito = True
                break
            elif (codigo1 & codigo2) != 0:
                # Ambos do mesmo lado de fora (AND != 0): rejeita sem calcular interseção
                break
            else:
                # Caso parcial: escolhe o ponto que está fora e recorta até a borda
                # indicada pelo bit mais significativo do seu código
                codigo_fora = codigo1 if codigo1 != 0 else codigo2

                # Calcula a interseção com a borda correspondente ao bit ativo.
                # Usa a equação paramétrica da reta: P = P1 + t*(P2-P1)
                if codigo_fora & 1:   # ESQUERDA: x = xmin
                    x = xmin
                    y = y1 + (y2 - y1) * (xmin - x1) / (x2 - x1)
                elif codigo_fora & 2: # DIREITA: x = xmax
                    x = xmax
                    y = y1 + (y2 - y1) * (xmax - x1) / (x2 - x1)
                elif codigo_fora & 4: # SUPERIOR: y = ymin
                    y = ymin
                    x = x1 + (x2 - x1) * (ymin - y1) / (y2 - y1)
                elif codigo_fora & 8: # INFERIOR: y = ymax
                    y = ymax
                    x = x1 + (x2 - x1) * (ymax - y1) / (y2 - y1)

                # Substitui o ponto externo pelo ponto de interseção e recalcula o código
                if codigo_fora == codigo1:
                    x1, y1 = x, y
                    codigo1 = calcular_codigo(x1, y1)
                else:
                    x2, y2 = x, y
                    codigo2 = calcular_codigo(x2, y2)

        if aceito:
            return Reta(Ponto(x1, y1), Ponto(x2, y2), reta.cor)
        return None

    @staticmethod
    def liang_barsky(reta: Reta, xmin: float, ymin: float,
                     xmax: float, ymax: float) -> Optional[Reta]:
        """
        Algoritmo de Liang-Barsky.

        Parametriza a reta como P(u) = P1 + u*(P2 - P1), com u in [0, 1].
        Para cada uma das quatro bordas da janela define-se p[k] e q[k]
        tais que a condição p[k]*u <= q[k] representa estar do lado de dentro.

          p[k] < 0 -> a reta entra pela borda k -> atualiza u1 (limite de entrada)
          p[k] > 0 -> a reta sai pela borda k   -> atualiza u2 (limite de saída)
          p[k] = 0 -> reta paralela à borda k   -> rejeita se q[k] < 0 (fora)

        Se ao final u1 > u2, o intervalo visível é vazio e o segmento está
        completamente fora da janela. Caso contrário, reconstrói os extremos
        com base nos valores finais de u1 e u2.
        """
        x1, y1 = reta.p1.x, reta.p1.y
        x2, y2 = reta.p2.x, reta.p2.y
        dx = x2 - x1
        dy = y2 - y1

        # u1 e u2 delimitam o trecho visível: u=0 é P1 e u=1 é P2
        u1 = 0.0
        u2 = 1.0

        # p[k] e q[k] para cada borda: esquerda, direita, superior, inferior
        p = [-dx, dx, -dy, dy]
        q = [x1 - xmin, xmax - x1, y1 - ymin, ymax - y1]

        for i in range(4):
            if p[i] == 0:
                # Reta paralela a esta borda: rejeita se estiver fora do lado correspondente
                if q[i] < 0:
                    return None
            else:
                # Calcula o parâmetro u onde a reta cruza esta borda
                r = q[i] / p[i]
                if p[i] < 0:
                    # Reta entra pela borda (de fora para dentro): atualiza limite de entrada
                    if r > u2:
                        return None   # entrada ocorre depois da saída: segmento invisível
                    if r > u1:
                        u1 = r
                else:
                    # Reta sai pela borda (de dentro para fora): atualiza limite de saída
                    if r < u1:
                        return None   # saída ocorre antes da entrada: segmento invisível
                    if r < u2:
                        u2 = r

        # Reconstrói os extremos recortados a partir de u1 e u2.
        # A ordem importa: u2 deve ser calculado antes de sobrescrever x1/y1.
        if u2 < 1.0:
            x2 = x1 + u2 * dx
            y2 = y1 + u2 * dy
        if u1 > 0.0:
            x1 = x1 + u1 * dx
            y1 = y1 + u1 * dy

        return Reta(Ponto(x1, y1), Ponto(x2, y2), reta.cor)