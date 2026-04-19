"""
Transformações Geométricas 2D.

O sistema de coordenadas é o da tela: origem no canto superior esquerdo,
Y cresce para baixo. Por isso os eixos de reflexão e o pivot de rotação/escala
são passados como parâmetros (geralmente o centro da tela), não fixos na origem.
"""

import math
from typing import Union
from .formas import Ponto, Reta, Poligono


class Transformador:
    """Aplica transformações geométricas 2D a primitivas (Reta e Poligono)."""

    @staticmethod
    def transladar(primitiva: Union[Reta, Poligono], dx: float, dy: float) -> Union[Reta, Poligono]:
        """
        Translação: desloca a primitiva somando (dx, dy) a cada ponto.
        Não depende de nenhum pivot - todos os pontos se movem igualmente.
        """
        def transladar_ponto(p: Ponto) -> Ponto:
            return Ponto(p.x + dx, p.y + dy)

        return Transformador._aplicar_a_pontos(primitiva, transladar_ponto)

    @staticmethod
    def rotacionar(primitiva: Union[Reta, Poligono], cx: float, cy: float,
                   angulo_graus: float) -> Union[Reta, Poligono]:
        """
        Rotação em torno do ponto (cx, cy).

        Segue o padrão TRT⁻¹ (translada para a origem, rotaciona, translada de volta):
          1. Subtrai o pivot para mover o centro de rotação para a origem
          2. Aplica a matriz de rotação 2D:
               x' = x*cos - y*sin
               y' = x*sin + y*cos
          3. Soma o pivot de volta

        Ângulo positivo rotaciona no sentido horário na tela (pois Y cresce para baixo).
        """
        angulo_rad = math.radians(angulo_graus)
        cos_a = math.cos(angulo_rad)
        sin_a = math.sin(angulo_rad)

        def rotacionar_ponto(p: Ponto) -> Ponto:
            # Passo 1: translada para a origem
            x = p.x - cx
            y = p.y - cy
            # Passo 2: aplica a matriz de rotação
            x_rot = x * cos_a - y * sin_a
            y_rot = x * sin_a + y * cos_a
            # Passo 3: translada de volta
            return Ponto(x_rot + cx, y_rot + cy)

        return Transformador._aplicar_a_pontos(primitiva, rotacionar_ponto)

    @staticmethod
    def escalar(primitiva: Union[Reta, Poligono], cx: float, cy: float,
                sx: float, sy: float) -> Union[Reta, Poligono]:
        """
        Escala em torno do ponto (cx, cy).

        Também segue o padrão TRT⁻¹: translada para a origem, aplica o fator
        de escala em cada eixo separadamente, translada de volta.
        sx e sy independentes permitem escala não-uniforme (deformação).
        """
        def escalar_ponto(p: Ponto) -> Ponto:
            # Passo 1: translada para a origem
            x = p.x - cx
            y = p.y - cy
            # Passo 2: aplica os fatores de escala
            x_esc = x * sx
            y_esc = y * sy
            # Passo 3: translada de volta
            return Ponto(x_esc + cx, y_esc + cy)

        return Transformador._aplicar_a_pontos(primitiva, escalar_ponto)

    @staticmethod
    def refletir_x(primitiva: Union[Reta, Poligono], eixo_y: float) -> Union[Reta, Poligono]:
        """
        Reflexão em relação à reta horizontal y = eixo_y (espelho horizontal).

        Inverte y em relação ao eixo: y' = 2*eixo_y - y.
        O eixo é passado como parâmetro (não fixo em y=0) porque o sistema de
        coordenadas da tela não tem um eixo natural visível na origem.
        """
        def refletir_ponto(p: Ponto) -> Ponto:
            return Ponto(p.x, 2 * eixo_y - p.y)

        return Transformador._aplicar_a_pontos(primitiva, refletir_ponto)

    @staticmethod
    def refletir_y(primitiva: Union[Reta, Poligono], eixo_x: float) -> Union[Reta, Poligono]:
        """
        Reflexão em relação à reta vertical x = eixo_x (espelho vertical).

        Inverte x em relação ao eixo: x' = 2*eixo_x - x.
        """
        def refletir_ponto(p: Ponto) -> Ponto:
            return Ponto(2 * eixo_x - p.x, p.y)

        return Transformador._aplicar_a_pontos(primitiva, refletir_ponto)

    @staticmethod
    def refletir_xy(primitiva: Union[Reta, Poligono], cx: float, cy: float) -> Union[Reta, Poligono]:
        """
        Reflexão pontual em relação ao ponto (cx, cy).

        Equivale a uma rotação de 180° em torno de (cx, cy), ou a aplicar
        refletir_x e refletir_y em sequência.
        Inverte as duas coordenadas: x' = 2*cx - x,  y' = 2*cy - y.
        """
        def refletir_ponto(p: Ponto) -> Ponto:
            return Ponto(2 * cx - p.x, 2 * cy - p.y)

        return Transformador._aplicar_a_pontos(primitiva, refletir_ponto)

    @staticmethod
    def _aplicar_a_pontos(primitiva: Union[Reta, Poligono],
                          funcao_transformacao) -> Union[Reta, Poligono]:
        """
        Distribui uma transformação de ponto para todos os pontos de uma primitiva.

        Cada transformação define apenas "como mover um Ponto" e este 
        método cuida de aplicar isso corretamente à estrutura da primitiva,
        seja ela uma Reta (2 pontos) ou um Poligono (n vértices).
        Sempre retorna uma nova instância, sem modificar a original.
        """
        if isinstance(primitiva, Reta):
            # Transforma os dois extremos e preserva a cor
            return Reta(
                funcao_transformacao(primitiva.p1),
                funcao_transformacao(primitiva.p2),
                primitiva.cor
            )
        elif isinstance(primitiva, Poligono):
            # Transforma cada vértice preservando a ordem, a cor e o atributo fechado
            novos_vertices = [funcao_transformacao(p) for p in primitiva.vertices]
            return Poligono(novos_vertices, primitiva.cor, primitiva.fechado)
        else:
            # Tipo desconhecido: retorna sem modificar
            return primitiva