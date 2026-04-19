"""
Estruturas de dados e gerenciador de desenho.

Define as primitivas geométricas (Ponto, Reta, Poligono) e a classe Desenho,
que centraliza todas as primitivas da cena e aplica recorte não-destrutivo.
"""

from dataclasses import dataclass
from typing import List, Tuple, Optional
import math


# ---------------------------------------------------------------------------
# Primitivas
# ---------------------------------------------------------------------------

@dataclass
class Ponto:
    x: float
    y: float

    def __hash__(self):
        # Necessário para usar Ponto como chave de dicionário ou elemento de conjunto
        return hash((self.x, self.y))

    def __eq__(self, other):
        # Compara com tolerância para evitar problemas de ponto flutuante
        if isinstance(other, Ponto):
            return abs(self.x - other.x) < 0.001 and abs(self.y - other.y) < 0.001
        return False


@dataclass
class Reta:
    p1: Ponto   # ponto inicial
    p2: Ponto   # ponto final
    cor: Tuple[int, int, int] = (0, 0, 0)

    def copiar(self):
        # Retorna uma cópia independente da reta para garantir que transformações 
        # não alterem a instância original
        return Reta(Ponto(self.p1.x, self.p1.y),
                    Ponto(self.p2.x, self.p2.y),
                    self.cor)


@dataclass
class Poligono:
    vertices: List[Ponto]
    cor: Tuple[int, int, int] = (0, 0, 0)
    fechado: bool = True  # se True, conecta o último vértice ao primeiro

    def copiar(self):
        # Cria uma cópia independente com novos objetos Ponto para cada vértice
        return Poligono([Ponto(p.x, p.y) for p in self.vertices],
                        self.cor, self.fechado)

    def get_retas(self):
        # Gera as arestas do polígono dinamicamente a partir dos vértices.
        # O operador % n garante que o último vértice conecta ao primeiro,
        # fechando o polígono sem precisar duplicar o ponto inicial na lista.
        n = len(self.vertices)
        return [Reta(self.vertices[i], self.vertices[(i+1) % n], self.cor)
                for i in range(n)]


# ---------------------------------------------------------------------------
# Gerenciador
# ---------------------------------------------------------------------------

class Desenho:
    """
    Implementa recorte NÃO-DESTRUTIVO: as listas originais nunca são
    modificadas. O recorte é um filtro aplicado apenas na hora de retornar
    os dados para renderização, via properties. Isso permite ativar, trocar
    ou remover o recorte a qualquer momento sem perder nenhuma primitiva.

    Círculos não participam do recorte.
    """

    def __init__(self):
        from algoritmos.recorte import AlgoritmosRecorte
        self._AlgoritmosRecorte = AlgoritmosRecorte

        # Listas originais - nunca modificadas pelo recorte
        self._retas_originais:    List[Reta]     = []
        self._circulos_originais: List[dict]     = []
        self._poligonos:          List[Poligono] = []

        # Janela de recorte ativa, ou None se nenhum recorte estiver definido
        self._recorte: Optional[Tuple[float, float, float, float]] = None  # (xmin, ymin, xmax, ymax)
        self.algoritmo_recorte: str = 'cohen_sutherland'

        # Lista de itens atualmente selecionados - cada entrada é ('tipo', índice, primitiva)
        self.itens_selecionados: List = []

    # ------------------------------------------------------------------
    # Properties públicas - aplicam o filtro de recorte na leitura
    # ------------------------------------------------------------------

    @property
    def retas(self) -> List[Reta]:
        # Sem recorte ativo: retorna todas as retas originais.
        # Com recorte: passa cada reta pelo algoritmo selecionado e descarta
        # as que estão completamente fora da janela. As que cruzam a borda
        # retornam já com os pontos ajustados para o limite da janela.
        if self._recorte is None:
            return list(self._retas_originais)
        xmin, ymin, xmax, ymax = self._recorte
        return [rc for r in self._retas_originais
                if (rc := self._recortar_reta(r, xmin, ymin, xmax, ymax)) is not None]

    @property
    def poligonos(self) -> List[Poligono]:
        # Polígonos brutos - o recorte é aplicado aresta por aresta em
        # arestas_poligonos_visiveis(), não aqui, para preservar o índice original
        return list(self._poligonos)

    def arestas_poligonos_visiveis(self) -> List[Tuple['Reta', int]]:
        # Retorna cada aresta visível junto com o índice do seu polígono de origem.
        # O índice é necessário para o paint.py saber se o polígono está selecionado.
        # O recorte é aplicado aresta por aresta: arestas completamente fora são
        # descartadas e as que cruzam a borda retornam já recortadas.
        if self._recorte is None:
            return [(aresta, i)
                    for i, poly in enumerate(self._poligonos)
                    for aresta in poly.get_retas()]
        xmin, ymin, xmax, ymax = self._recorte
        resultado = []
        for i, poly in enumerate(self._poligonos):
            for aresta in poly.get_retas():
                rc = self._recortar_reta(aresta, xmin, ymin, xmax, ymax)
                if rc is not None:
                    resultado.append((rc, i))
        return resultado

    @property
    def circulos(self) -> List[dict]:
        # Círculos não participam do filtro de recorte - são sempre desenhados
        # por completo via Bresenham. O campo 'arcos' = None instrui o paint.py
        # a usar o rasterizador ao invés de drawArc do Qt.
        return [{**c, 'arcos': None} for c in self._circulos_originais]

    # ------------------------------------------------------------------
    # Adicionar primitivas
    # ------------------------------------------------------------------

    def adicionar_reta(self, reta: Reta):
        # Armazena uma cópia para que alterações externas não afetem o gerenciador
        self._retas_originais.append(reta.copiar())

    def adicionar_poligono(self, poligono: Poligono):
        self._poligonos.append(poligono.copiar())

    def adicionar_circulo(self, xc: int, yc: int, r: int, cor):
        # Círculos são armazenados como dicionário porque não são compostos de
        # Pontos - o Transformador e o Rasterizador os tratam separadamente
        self._circulos_originais.append({'xc': xc, 'yc': yc, 'r': r, 'cor': cor})

    # ------------------------------------------------------------------
    # Recorte não-destrutivo
    # ------------------------------------------------------------------

    def definir_recorte(self, xmin: float, ymin: float,
                        xmax: float, ymax: float):
        # Ativa a janela de recorte. O próximo redesenho já filtra pelas novas bordas.
        self._recorte = (xmin, ymin, xmax, ymax)

    def limpar_recorte(self):
        # Remove o filtro de recorte - o próximo redesenho mostra tudo novamente
        self._recorte = None

    def recortar_retas(self, xmin: float, ymin: float,
                       xmax: float, ymax: float,
                       algoritmo: str = 'cohen_sutherland'):
        # Define o algoritmo e ativa a janela de recorte em uma única chamada
        self.algoritmo_recorte = algoritmo
        self.definir_recorte(xmin, ymin, xmax, ymax)

    # ------------------------------------------------------------------
    # Recorte de reta (despacha para o algoritmo selecionado)
    # ------------------------------------------------------------------

    def _recortar_reta(self, reta: Reta, xmin, ymin, xmax, ymax):
        # Despacha para Cohen-Sutherland ou Liang-Barsky conforme escolha do usuário.
        # Ambos retornam uma nova Reta com pontos ajustados, ou None se fora da janela.
        if self.algoritmo_recorte == 'liang_barsky':
            return self._AlgoritmosRecorte.liang_barsky(reta, xmin, ymin, xmax, ymax)
        return self._AlgoritmosRecorte.cohen_sutherland(reta, xmin, ymin, xmax, ymax)

    # ------------------------------------------------------------------
    # Seleção por região retangular
    # ------------------------------------------------------------------

    def selecionar_em_retangulo(self, ret_min: Ponto, ret_max: Ponto) -> List:
        # Retorna todas as primitivas que *tocam* o retângulo de seleção -
        # não apenas as que estão completamente dentro dele.
        # Retas e arestas de polígonos usam Cohen-Sutherland como teste de interseção.
        # Círculos usam distância mínima/máxima ao centro (ver _circulo_toca).
        selecionados = []
        for i, reta in enumerate(self._retas_originais):
            if self._reta_toca(reta, ret_min, ret_max):
                selecionados.append(('reta', i, reta))
        for i, poly in enumerate(self._poligonos):
            if self._poly_toca(poly, ret_min, ret_max):
                selecionados.append(('poligono', i, poly))
        for i, circ in enumerate(self._circulos_originais):
            if self._circulo_toca(circ, ret_min, ret_max):
                selecionados.append(('circulo', i, circ))
        return selecionados

    @staticmethod
    def _reta_toca(reta: Reta, rmin: Ponto, rmax: Ponto) -> bool:
        # Reutiliza a lógica de Cohen-Sutherland como teste booleano de interseção:
        # se o algoritmo não rejeita o segmento, ele toca o retângulo.
        x1, y1 = reta.p1.x, reta.p1.y
        x2, y2 = reta.p2.x, reta.p2.y
        xmin, ymin, xmax, ymax = rmin.x, rmin.y, rmax.x, rmax.y

        def codigo(x, y):
            # Cada bit representa uma região fora da janela:
            # bit 0 = esquerda, bit 1 = direita, bit 2 = abaixo, bit 3 = acima
            c = 0
            if x < xmin: c |= 1
            elif x > xmax: c |= 2
            if y < ymin: c |= 4
            elif y > ymax: c |= 8
            return c

        c1, c2 = codigo(x1, y1), codigo(x2, y2)

        while True:
            if c1 == 0 and c2 == 0:
                return True   # ambos dentro: segmento toca o retângulo
            if c1 & c2:
                return False  # mesmo lado de fora: definitivamente não toca
            # Recorta o ponto externo contra a borda indicada pelo bit ativo
            cf = c1 if c1 else c2
            if cf & 1:
                x, y = xmin, y1 + (y2 - y1) * (xmin - x1) / (x2 - x1)
            elif cf & 2:
                x, y = xmax, y1 + (y2 - y1) * (xmax - x1) / (x2 - x1)
            elif cf & 4:
                y, x = ymin, x1 + (x2 - x1) * (ymin - y1) / (y2 - y1)
            else:
                y, x = ymax, x1 + (x2 - x1) * (ymax - y1) / (y2 - y1)
            if cf == c1:
                x1, y1, c1 = x, y, codigo(x, y)
            else:
                x2, y2, c2 = x, y, codigo(x, y)

    @staticmethod
    def _poly_toca(poly: Poligono, rmin: Ponto, rmax: Ponto) -> bool:
        # Um polígono toca o retângulo se ao menos uma de suas arestas tocar.
        # Isso cobre tanto arestas que cruzam a borda quanto polígonos que
        # contêm o retângulo inteiramente dentro deles.
        for aresta in poly.get_retas():
            if Desenho._reta_toca(aresta, rmin, rmax):
                return True
        return False

    @staticmethod
    def _circulo_toca(circ: dict, rmin: Ponto, rmax: Ponto) -> bool:
        # O arco do círculo toca o retângulo se e somente se:
        #   dist_min <= r  -> o retângulo chega até o raio (arco alcança o retângulo)
        #   dist_max >= r  -> o retângulo não engloba o círculo inteiro
        # Juntas, as duas condições garantem que o arco de fato cruza a região.
        xc, yc, r = circ['xc'], circ['yc'], circ['r']
        xmin, ymin, xmax, ymax = rmin.x, rmin.y, rmax.x, rmax.y

        # Ponto do retângulo mais próximo do centro (clamp nas duas coordenadas)
        px = max(xmin, min(xc, xmax))
        py = max(ymin, min(yc, ymax))
        dist_min = math.hypot(px - xc, py - yc)

        # Ponto mais distante é sempre um dos quatro cantos do retângulo
        dist_max = max(
            math.hypot(xmin - xc, ymin - yc),
            math.hypot(xmax - xc, ymin - yc),
            math.hypot(xmin - xc, ymax - yc),
            math.hypot(xmax - xc, ymax - yc),
        )

        return dist_min <= r <= dist_max

    # ------------------------------------------------------------------
    # Ações gerais
    # ------------------------------------------------------------------

    def limpar_tudo(self):
        # Reseta completamente a cena, incluindo seleção e recorte
        self._retas_originais.clear()
        self._poligonos.clear()
        self._circulos_originais.clear()
        self._recorte = None
        self.itens_selecionados = []

GerenciadorDesenho = Desenho