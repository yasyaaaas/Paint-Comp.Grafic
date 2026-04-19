"""
Algoritmos de rasterização de linhas e círculos.

Todos os algoritmos operam em coordenadas de tela (origem no canto superior
esquerdo, Y cresce para baixo) e escrevem os pixels via callback, sem
nenhuma dependência do Qt ou de qualquer biblioteca gráfica.
"""

from typing import Tuple, Callable


class Rasterizador:
    """
    Rasteriza primitivas geométricas pixel a pixel.

    Recebe no construtor um callback desenhar_pixel(x, y) que define
    o que fazer com cada pixel calculado. Dessa forma o rasterizador
    é completamente independente da biblioteca gráfica utilizada.
    """

    def __init__(self, callback_desenhar_pixel: Callable):
        self.desenhar_pixel = callback_desenhar_pixel
        self.cor_atual = (0, 0, 0)

    def definir_cor(self, cor: Tuple[int, int, int]):
        """Define a cor atual de desenho (RGB)."""
        self.cor_atual = cor

    # ------------------------------------------------------------------
    # Rasterização de retas
    # ------------------------------------------------------------------

    def desenhar_reta_dda(self, x1: int, y1: int, x2: int, y2: int):
        """
        Algoritmo DDA.

        Calcula incrementos fracionários em x e y proporcionais ao maior
        deslocamento entre os dois eixos, garantindo que não haja lacunas
        (sempre avança 1 pixel por vez no eixo dominante).
        Usa ponto flutuante, mais simples de entender, menos eficiente
        que Bresenham para execução em hardware.
        """
        dx = x2 - x1
        dy = y2 - y1

        # O eixo com maior deslocamento determina quantos passos serão dados.
        # Isso garante que o incremento no eixo dominante seja exatamente 1 (ou -1),
        # sem lacunas nem pixels duplos.
        if abs(dx) > abs(dy):
            passos = abs(dx)
        else:
            passos = abs(dy)

        # Caso especial: ponto único, sem deslocamento em nenhum eixo
        if passos == 0:
            self.desenhar_pixel(x1, y1)
            return

        # Incremento fracionário em cada eixo: sempre <= 1 em módulo
        x_inc = dx / passos
        y_inc = dy / passos

        x = float(x1)
        y = float(y1)

        # A cada passo, arredonda para o pixel mais próximo e avança
        for _ in range(passos + 1):
            self.desenhar_pixel(int(round(x)), int(round(y)))
            x += x_inc
            y += y_inc

    def desenhar_reta_bresenham(self, x1: int, y1: int, x2: int, y2: int):
        """
        Algoritmo de Bresenham para retas.

        Opera exclusivamente com aritmética inteira (sem divisão ou ponto
        flutuante), o que o torna muito eficiente. A ideia central é manter
        um parâmetro de decisão p que acumula o erro entre a reta ideal e a
        grade de pixels. Quando p >= 0, o erro passou de meio pixel e o eixo
        secundário avança.

        Dois casos cobrem todas as inclinações:
          dx > dy  -> reta mais horizontal: avança sempre em x, decide em y
          dy >= dx -> reta mais vertical:   avança sempre em y, decide em x
        """
        dx = abs(x2 - x1)
        dy = abs(y2 - y1)

        # Direção do passo em cada eixo (+1 para crescente, -1 para decrescente)
        passo_x = 1 if x2 > x1 else -1
        passo_y = 1 if y2 > y1 else -1

        x = x1
        y = y1

        if dx > dy:
            # Caso horizontal: avança sempre em x, y só sobe quando p >= 0
            # p inicial = 2*dy - dx  (meio pixel de erro já considerado)
            p = 2 * dy - dx
            const1 = 2 * dy        # incremento de p quando não muda y (p < 0)
            const2 = 2 * (dy - dx) # incremento de p quando muda y    (p >= 0)

            for _ in range(dx + 1):
                self.desenhar_pixel(x, y)
                if p < 0:
                    # Erro ainda menor que meio pixel: mantém y
                    p += const1
                else:
                    # Erro passou de meio pixel: avança y e corrige o acúmulo
                    y += passo_y
                    p += const2
                x += passo_x
        else:
            # Caso vertical: avança sempre em y, x só avança quando p >= 0
            p = 2 * dx - dy
            const1 = 2 * dx
            const2 = 2 * (dx - dy)

            for _ in range(dy + 1):
                self.desenhar_pixel(x, y)
                if p < 0:
                    p += const1
                else:
                    x += passo_x
                    p += const2
                y += passo_y

    # ------------------------------------------------------------------
    # Rasterização de círculos
    # ------------------------------------------------------------------

    def desenhar_circulo_bresenham(self, xc: int, yc: int, r: int):
        """
        Algoritmo de Bresenham para círculos (algoritmo do ponto médio).

        Em vez de calcular os 360° do círculo, percorre apenas o primeiro
        octante (de 0° a 45°, onde x vai de 0 até y) e usa a simetria de
        8 octantes para espelhar cada ponto calculado nas outras 7 posições.
        O custo total é proporcional a r, não a r².

        O parâmetro de decisão p = 3 - 2r determina, a cada passo de x,
        se y deve diminuir (p >= 0) ou permanecer igual (p < 0).
        """
        x = 0
        y = r
        # Parâmetro de decisão inicial derivado da equação do círculo x²+y²=r²
        # avaliada no ponto médio entre (0, r) e (1, r): p0 = 3 - 2r
        p = 3 - 2 * r

        # Desenha o ponto inicial (topo do círculo) e seus 7 simétricos
        self._desenhar_pontos_circulo(xc, yc, x, y)

        # Percorre até x == y (45°): a partir daí a simetria já cobre o restante
        while x < y:
            x += 1
            if p < 0:
                # y permanece: o ponto médio está dentro do círculo
                p = p + 4 * x + 6
            else:
                # y diminui: o ponto médio está fora do círculo
                y -= 1
                p = p + 4 * (x - y) + 10

            self._desenhar_pontos_circulo(xc, yc, x, y)

    def _desenhar_pontos_circulo(self, xc: int, yc: int, x: int, y: int):
        """
        Desenha os 8 pontos simétricos correspondentes a um ponto (x, y)
        no primeiro octante, um ponto por octante.

        As primeiras 4 linhas usam (±x, ±y) e as últimas 4 trocam x e y,
        cobrindo os octantes que estão entre 45° e 90°.
        """
        self.desenhar_pixel(xc + x, yc + y)
        self.desenhar_pixel(xc - x, yc + y)
        self.desenhar_pixel(xc + x, yc - y)
        self.desenhar_pixel(xc - x, yc - y)
        # Troca x e y para cobrir os outros 4 octantes (reflexão pela diagonal)
        self.desenhar_pixel(xc + y, yc + x)
        self.desenhar_pixel(xc - y, yc + x)
        self.desenhar_pixel(xc + y, yc - x)
        self.desenhar_pixel(xc - y, yc - x)