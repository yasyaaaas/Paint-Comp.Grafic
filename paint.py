"""
Tela de Desenho - canvas principal da aplicação.

Responsável por:
  - Capturar eventos de mouse e despachar para o modo de desenho ativo
  - Manter o buffer de pixels (QPixmap) e acionar o rasterizador
  - Redesenhar toda a cena a partir dos dados do gerenciador
  - Aplicar transformações nas primitivas selecionadas
"""

import math
from typing import Optional

from PyQt5.QtWidgets import QWidget, QSizePolicy, QMessageBox
from PyQt5.QtCore import Qt, QRect, QPoint
from PyQt5.QtGui import QPainter, QPen, QColor, QBrush, QPixmap, QPalette

from algoritmos.formas import Ponto, Reta, Poligono, GerenciadorDesenho
from algoritmos.rasterizacao import Rasterizador
from algoritmos.transform import Transformador
from curvas.bezier import CurvaBezier
from curvas.hermite import CurvaHermite

ESPESSURA_LINHA = 2
COR_SELECIONADO = QColor(255, 140, 0)  # laranja para destacar itens selecionados


class Paint(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(600, 500)
        self.setBackgroundRole(QPalette.Base)
        self.setAutoFillBackground(True)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.gerenciador = GerenciadorDesenho()  # armazena e filtra todas as primitivas
        self.modo_desenho = "reta"               # modo atual da ferramenta ativa

        self.ponto_inicio = None         # primeiro clique pendente (reta ou círculo)
        self.pontos_poligono: list = []  # vértices coletados do polígono em construção

        # Pontos de controle coletados para a curva em construção.
        # Bézier: qualquer número de pontos - extremos são interpolados, intermediários atraem.
       # Hermite: exatamente 4 pontos: [P0, R0, R1, P1].
        # Em ambos os casos a curva só é finalizada ao clicar em "Finalizar Curva".
        self.pontos_curva: list = []

        # Listas persistentes de curvas já finalizadas.
        # Cada entrada é um dict com os pontos de controle e a cor usada.
        self._curvas_bezier:      list = []  # [{pontos: [(x,y)…], cor: (r,g,b)}]
        self._curvas_hermite: list = []      # [{pontos: [(x,y)…], cor: (r,g,b)}]

        self.cor_foreground = QColor(0, 0, 0)
        self.cor_background = QColor(255, 255, 255)

        # Estado da seleção retangular (arrastar para selecionar)
        self.selecionando = False
        self.inicio_selecao: Optional[QPoint] = None
        self.fim_selecao:   Optional[QPoint] = None

        # Estado do recorte retangular (arrastar para definir janela de recorte)
        self.recortando = False
        self.inicio_recorte: Optional[QPoint] = None
        self.fim_recorte:   Optional[QPoint] = None

        self.algoritmo_reta    = "bresenham"        # algoritmo de rasterização de retas
        self.algoritmo_recorte = "cohen_sutherland" # algoritmo de recorte de segmentos

        # QPixmap é o buffer de desenho em memória.
        # Os algoritmos escrevem pixels nele via _pixel_cb e o paintEvent
        # simplesmente copia o buffer inteiro na janela. Isso separa a lógica
        # de rasterização da lógica de exibição do Qt.
        self.pixmap = QPixmap(self.size())
        self.pixmap.fill(Qt.white)

        self.rasterizador = Rasterizador(self._pixel_cb)

        # Instâncias dos renderizadores de curvas - recebem _rasterizar_reta como
        # callback para que respeitem o algoritmo de reta escolhido pelo usuário.
        self.bezier = CurvaBezier(self._rasterizar_reta)
        self.hermite = CurvaHermite(self._rasterizar_reta)

        self.setMouseTracking(True)

    # ------------------------------------------------------------------
    # Helpers internos
    # ------------------------------------------------------------------

    def _cor_rgb(self):
        c = self.cor_foreground
        return (c.red(), c.green(), c.blue())

    def _definir_cor_rasterizador(self):
        self.rasterizador.definir_cor(self._cor_rgb())

    def _rasterizar_reta(self, x1, y1, x2, y2):
        # Despacha para o algoritmo escolhido pelo usuário na toolbar
        self._definir_cor_rasterizador()
        if self.algoritmo_reta == 'dda':
            self.rasterizador.desenhar_reta_dda(x1, y1, x2, y2)
        else:
            self.rasterizador.desenhar_reta_bresenham(x1, y1, x2, y2)

    def _pixel_cb(self, x: int, y: int):
        # Callback chamado pelo Rasterizador uma vez por pixel calculado.
        # Desenha um pequeno círculo centrado no pixel em vez de um ponto único,
        # porque drawPoint produz traços muito finos visualmente na escala usada.
        painter = QPainter(self.pixmap)
        painter.setPen(QPen(self.cor_foreground, ESPESSURA_LINHA))
        painter.drawEllipse(x - ESPESSURA_LINHA//2, y - ESPESSURA_LINHA//2,
                            ESPESSURA_LINHA, ESPESSURA_LINHA)
        painter.end()

    # ------------------------------------------------------------------
    # Resize
    # ------------------------------------------------------------------

    def resizeEvent(self, event):
        # Ao redimensionar a janela, cria um novo pixmap do tamanho correto
        # e copia o conteúdo anterior para preservar o desenho já feito.
        novo = QPixmap(self.size())
        novo.fill(Qt.white)
        p = QPainter(novo)
        p.drawPixmap(0, 0, self.pixmap)
        p.end()
        self.pixmap = novo
        super().resizeEvent(event)

    # ------------------------------------------------------------------
    # Redesenha tudo a partir do gerenciador
    # ------------------------------------------------------------------

    def redesenhar_tudo(self):
        # Apaga o buffer inteiro e rasteriza todas as primitivas novamente do zero.
        self.pixmap.fill(self.cor_background)

        # Conjunto de (tipo, índice) dos itens selecionados para checagem rápida
        selecionados_idx = {
            (item[0], item[1]) for item in self.gerenciador.itens_selecionados
        }

        # --- Retas ---
        # gerenciador.retas já aplica o filtro de recorte se houver janela ativa
        for i, reta in enumerate(self.gerenciador.retas):
            self.cor_foreground = COR_SELECIONADO if ('reta', i) in selecionados_idx else QColor(*reta.cor)
            self._rasterizar_reta(int(reta.p1.x), int(reta.p1.y),
                                  int(reta.p2.x), int(reta.p2.y))

        # --- Polígonos ---
        # arestas_poligonos_visiveis() aplica o recorte aresta por aresta
        # e retorna o índice do polígono de origem junto com cada aresta
        selecionados_poly = {item[1] for item in self.gerenciador.itens_selecionados
                             if item[0] == 'poligono'}
        for aresta, poly_idx in self.gerenciador.arestas_poligonos_visiveis():
            self.cor_foreground = COR_SELECIONADO if poly_idx in selecionados_poly else QColor(*aresta.cor)
            self._rasterizar_reta(int(aresta.p1.x), int(aresta.p1.y),
                                  int(aresta.p2.x), int(aresta.p2.y))

        # --- Círculos ---
        # Círculos não participam do recorte: arcos é sempre None.
        # São desenhados inteiramente via Bresenham pixel a pixel.
        circulos = self.gerenciador.circulos
        for i, circ in enumerate(circulos):
            if circ.get('arcos') is not None:
                continue  # salvaguarda: nunca deve ocorrer com a implementação atual
            self.cor_foreground = COR_SELECIONADO if ('circulo', i) in selecionados_idx else QColor(*circ['cor'])
            self._definir_cor_rasterizador()
            self.rasterizador.desenhar_circulo_bresenham(circ['xc'], circ['yc'], circ['r'])

        # --- Curvas de Bezier ---
        # Cada entrada armazena a lista de pontos de controle e a cor do momento do clique.
        # O grau da curva é (n − 1) para n pontos. Os extremos são interpolados;
        for curva in self._curvas_bezier:
            self.cor_foreground = QColor(*curva['cor'])
            self._definir_cor_rasterizador()
            self.bezier.desenhar(curva['pontos'])

        # --- Curvas de Hermite ---
        # Cada curva espera exatamente 4 pontos: [P0, R0, R1, P1]
        for curva in self._curvas_hermite:
            self.cor_foreground = QColor(*curva['cor'])
            self._definir_cor_rasterizador()
            self.hermite.desenhar(curva['pontos'])

        self.update()

    # ------------------------------------------------------------------
    # Paint event
    # ------------------------------------------------------------------

    def paintEvent(self, event):
        # Copia o buffer (pixmap) na janela e desenha os overlays temporários por cima.
        # Os overlays (retângulo de seleção, retângulo de recorte, preview do polígono)
        # não são gravados no buffer - existem apenas enquanto o mouse está pressionado.
        painter = QPainter(self)
        painter.drawPixmap(0, 0, self.pixmap)

        # Preview dos segmentos do polígono em construção (linha tracejada)
        if self.pontos_poligono:
            painter.setPen(QPen(self.cor_foreground, ESPESSURA_LINHA, Qt.DashLine))
            for i in range(len(self.pontos_poligono) - 1):
                p1, p2 = self.pontos_poligono[i], self.pontos_poligono[i + 1]
                painter.drawLine(p1.x(), p1.y(), p2.x(), p2.y())

        # Preview dos pontos de controle da curva em construção
        # Exibe pequenos círculos em cada ponto clicado e linhas conectando-os,
        # formando o polígono de controle visível enquanto o usuário ainda clica.
        if self.pontos_curva and self.modo_desenho in ("bezier", "hermite"):
            painter.setPen(QPen(QColor(120, 120, 220), 1, Qt.DashLine))
            for i, pt in enumerate(self.pontos_curva):
                # Pequeno marcador circular em cada ponto clicado
                painter.drawEllipse(pt[0] - 4, pt[1] - 4, 8, 8)
                if i > 0:
                    prev = self.pontos_curva[i - 1]
                    painter.drawLine(prev[0], prev[1], pt[0], pt[1])

        # Retângulo de seleção em azul semitransparente (overlay, não gravado no buffer)
        if self.selecionando and self.inicio_selecao and self.fim_selecao:
            painter.setPen(QPen(QColor(0, 0, 255), 1, Qt.DashLine))
            painter.setBrush(QBrush(QColor(0, 0, 255, 40)))
            painter.drawRect(QRect(self.inicio_selecao, self.fim_selecao))

        # Retângulo de recorte em vermelho semitransparente (overlay, não gravado no buffer)
        if self.recortando and self.inicio_recorte and self.fim_recorte:
            painter.setPen(QPen(QColor(220, 0, 0), 2, Qt.DashLine))
            painter.setBrush(QBrush(QColor(220, 0, 0, 25)))
            painter.drawRect(QRect(self.inicio_recorte, self.fim_recorte))

        painter.end()

    # ------------------------------------------------------------------
    # Mouse
    # ------------------------------------------------------------------

    def mousePressEvent(self, event):
        if event.button() != Qt.LeftButton:
            return
        pos = event.pos()
        x, y = pos.x(), pos.y()
        # Despacha para o handler correspondente ao modo de desenho ativo
        handler = {
            "reta":         lambda: self._press_reta(x, y),
            "circulo":      lambda: self._press_circulo(x, y),
            "poligono":     lambda: self._press_poligono(pos),
            "selecionar":   lambda: self._press_selecionar(pos),
            "recortar":     lambda: self._press_recortar(pos),
            "bezier":       lambda: self._press_curva(x, y),
            "hermite":      lambda: self._press_curva(x, y),
        }
        handler.get(self.modo_desenho, lambda: None)()

    def _press_reta(self, x, y):
        # Primeiro clique: registra o ponto inicial.
        # Segundo clique: rasteriza e salva a reta no gerenciador.
        if self.ponto_inicio is None:
            self.ponto_inicio = (x, y)
        else:
            x1, y1 = self.ponto_inicio
            self._rasterizar_reta(x1, y1, x, y)
            self.gerenciador.adicionar_reta(
                Reta(Ponto(x1, y1), Ponto(x, y), self._cor_rgb()))
            self.ponto_inicio = None
            self.redesenhar_tudo()

    def _press_circulo(self, x, y):
        # Primeiro clique: define o centro.
        # Segundo clique: calcula o raio pela distância euclidiana ao centro.
        if self.ponto_inicio is None:
            self.ponto_inicio = (x, y)
        else:
            xc, yc = self.ponto_inicio
            r = int(math.hypot(x - xc, y - yc))
            self._definir_cor_rasterizador()
            self.rasterizador.desenhar_circulo_bresenham(xc, yc, r)
            self.gerenciador.adicionar_circulo(xc, yc, r, self._cor_rgb())
            self.ponto_inicio = None
            self.redesenhar_tudo()

    def _press_poligono(self, pos):
        # Cada clique adiciona um vértice à lista temporária.
        # O polígono só é finalizado com botão "Finalizar Polígono".
        self.pontos_poligono.append(pos)
        self.update()

    def _press_selecionar(self, pos):
        # Inicia o arraste de seleção retangular
        self.selecionando = True
        self.inicio_selecao = self.fim_selecao = pos
        self.update()

    def _press_recortar(self, pos):
        # Inicia o arraste de definição da janela de recorte
        self.recortando = True
        self.inicio_recorte = self.fim_recorte = pos
        self.update()

    def _press_curva(self, x, y):
        # Cada clique adiciona um ponto de controle à lista temporária.
        # A curva só é rasterizada e salva ao clicar em "Finalizar Curva"
        self.pontos_curva.append((x, y))
        self.update()

    def mouseMoveEvent(self, event):
        # Atualiza o canto oposto do retângulo em tempo real enquanto o mouse se move
        if self.selecionando and self.inicio_selecao:
            self.fim_selecao = event.pos()
            self.update()
        if self.recortando and self.inicio_recorte:
            self.fim_recorte = event.pos()
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() != Qt.LeftButton:
            return

        if self.modo_desenho == "selecionar" and self.selecionando:
            self.selecionando = False
            # Normaliza o retângulo para que xmin < xmax e ymin < ymax,
            # independentemente da direção em que o usuário arrastou
            xmin = min(self.inicio_selecao.x(), self.fim_selecao.x())
            xmax = max(self.inicio_selecao.x(), self.fim_selecao.x())
            ymin = min(self.inicio_selecao.y(), self.fim_selecao.y())
            ymax = max(self.inicio_selecao.y(), self.fim_selecao.y())
            self.gerenciador.itens_selecionados = \
                self.gerenciador.selecionar_em_retangulo(Ponto(xmin, ymin), Ponto(xmax, ymax))
            n = len(self.gerenciador.itens_selecionados)
            self.inicio_selecao = self.fim_selecao = None
            self.redesenhar_tudo()
            msg = "Nenhum item selecionado." if n == 0 else f"{n} item(ns) selecionado(s)."
            QMessageBox.information(self, "Seleção", msg)

        elif self.modo_desenho == "recortar" and self.recortando:
            self.recortando = False
            # Normaliza o retângulo de recorte da mesma forma
            xmin = min(self.inicio_recorte.x(), self.fim_recorte.x())
            xmax = max(self.inicio_recorte.x(), self.fim_recorte.x())
            ymin = min(self.inicio_recorte.y(), self.fim_recorte.y())
            ymax = max(self.inicio_recorte.y(), self.fim_recorte.y())
            # Aplica o recorte não-destrutivo: apenas define a janela no gerenciador.
            # O redesenho que vem a seguir já usa o filtro para exibir apenas
            # os trechos visíveis, sem modificar as primitivas originais.
            self.gerenciador.recortar_retas(xmin, ymin, xmax, ymax, self.algoritmo_recorte)
            self.inicio_recorte = self.fim_recorte = None
            self.redesenhar_tudo()

    def mouseDoubleClickEvent(self, event):
        # Duplo clique finaliza o polígono ou a curva em construção
        if self.modo_desenho == "poligono":
            self.finalizar_poligono()
        elif self.modo_desenho in ("bezier", "hermite"):
            self.finalizar_curva()

    # ------------------------------------------------------------------
    # Ações públicas -> chamadas pela janela principal
    # ------------------------------------------------------------------

    def finalizar_poligono(self):
        # Precisa de pelo menos 3 vértices para formar um polígono fechado
        if len(self.pontos_poligono) >= 3:
            pontos = [Ponto(p.x(), p.y()) for p in self.pontos_poligono]
            self.gerenciador.adicionar_poligono(Poligono(pontos, self._cor_rgb()))
            self.redesenhar_tudo()
        self.pontos_poligono = []
        self.update()

    def finalizar_curva(self):
        """
        Finaliza a curva em construção.
        - Bézier: aceita 2 ou mais pontos.
        - Hermite: exige exatamente 4 pontos.
        """
        if not self.pontos_curva:
            return

        if self.modo_desenho == "bezier":
            if len(self.pontos_curva) < 2:
                QMessageBox.warning(self, "Aviso", "A curva Bézier precisa de pelo menos 2 pontos.")
                self.pontos_curva = []
                self.update()
                return
            entrada = {'pontos': list(self.pontos_curva), 'cor': self._cor_rgb()}
            self._curvas_bezier.append(entrada)

        elif self.modo_desenho == "hermite":   # <-- HERMITE
            if len(self.pontos_curva) != 4:
                QMessageBox.warning(self, "Aviso",
                                     "A curva Hermite exige exatamente 4 pontos:\n"
                                     "P0 (início), R0, R1, P1 (fim).")
                self.pontos_curva = []
                self.update()
                return
            entrada = {'pontos': list(self.pontos_curva), 'cor': self._cor_rgb()}
            self._curvas_hermite.append(entrada)

        self.pontos_curva = []
        self.redesenhar_tudo()

    def limpar_recorte(self):
        # Remove a janela de recorte e redesenha tudo sem filtro
        self.gerenciador.limpar_recorte()
        self.redesenhar_tudo()

    def limpar_tela(self):
        # Apaga todas as primitivas, o buffer e reseta o estado da ferramenta
        self.gerenciador.limpar_tudo()
        self.pixmap.fill(self.cor_background)
        self.pontos_poligono = []
        self.pontos_curva = []
        self.ponto_inicio = None
        self._curvas_bezier = []
        self._curvas_hermite = []
        self.gerenciador.itens_selecionados = []
        self.update()

    def transformar_selecionados(self, tipo: str, **kw):
        if not self.gerenciador.itens_selecionados:
            QMessageBox.warning(self, "Sem Seleção",
                                "Selecione itens primeiro usando a ferramenta Selecionar.")
            return

        # Mapa de nome de transformação para a função correspondente do Transformador.
        # Os parâmetros extras (pivot, ângulo, fatores) chegam via **kw.
        mapa = {
            "transladar":  lambda p: Transformador.transladar(p, kw['dx'], kw['dy']),
            "rotacionar":  lambda p: Transformador.rotacionar(p, kw['cx'], kw['cy'], kw['angulo']),
            "escalar":     lambda p: Transformador.escalar(p, kw['cx'], kw['cy'], kw['sx'], kw['sy']),
            "refletir_x":  lambda p: Transformador.refletir_x(p, kw['eixo_y']),
            "refletir_y":  lambda p: Transformador.refletir_y(p, kw['eixo_x']),
            "refletir_xy": lambda p: Transformador.refletir_xy(p, kw['cx'], kw['cy']),
        }
        fn = mapa.get(tipo, lambda p: p)

        # Aplica a transformação diretamente na lista original do gerenciador.
        # Círculos são tratados separadamente por não serem compostos de Pontos.
        for item in self.gerenciador.itens_selecionados:
            tipo_item, idx = item[0], item[1]
            if tipo_item == 'reta' and idx < len(self.gerenciador._retas_originais):
                self.gerenciador._retas_originais[idx] = fn(self.gerenciador._retas_originais[idx])
            elif tipo_item == 'poligono' and idx < len(self.gerenciador._poligonos):
                self.gerenciador._poligonos[idx] = fn(self.gerenciador._poligonos[idx])
            elif tipo_item == 'circulo' and idx < len(self.gerenciador._circulos_originais):
                self.gerenciador._circulos_originais[idx] = \
                    self._transformar_circulo(tipo, self.gerenciador._circulos_originais[idx], **kw)

        self.redesenhar_tudo()

    def _transformar_circulo(self, tipo: str, circ: dict, **kw) -> dict:
        """
        Aplica uma transformação geométrica a um círculo armazenado como dict.

        Círculos não são compostos de Pontos, então o Transformador não se aplica
        diretamente. Aqui apenas o centro (xc, yc) é transformado, e o raio
        só muda na escala (média de sx e sy para manter a forma circular).
        """
        xc, yc, r = circ["xc"], circ["yc"], circ["r"]

        if tipo == "transladar":
            # Translação: desloca apenas o centro, raio inalterado
            xc += kw["dx"]
            yc += kw["dy"]

        elif tipo == "rotacionar":
            # Rotação: move o centro em torno do pivot usando o Transformador.
            # O raio não muda porque rotação é uma transformação isométrica.
            centro = Transformador.rotacionar(
                Reta(Ponto(xc, yc), Ponto(xc, yc)), kw["cx"], kw["cy"], kw["angulo"])
            xc, yc = centro.p1.x, centro.p1.y

        elif tipo == "escalar":
            # Escala: move o centro proporcionalmente e ajusta o raio.
            # O raio usa a média de sx e sy para aproximar a escala em círculos
            # quando sx != sy (caso exato exigiria converter para elipse).
            cx, cy, sx, sy = kw["cx"], kw["cy"], kw["sx"], kw["sy"]
            xc = cx + (xc - cx) * sx
            yc = cy + (yc - cy) * sy
            r = int(r * (sx + sy) / 2)

        elif tipo == "refletir_x":
            # Reflexão horizontal: inverte y do centro em relação ao eixo
            yc = 2 * kw["eixo_y"] - yc

        elif tipo == "refletir_y":
            # Reflexão vertical: inverte x do centro em relação ao eixo
            xc = 2 * kw["eixo_x"] - xc

        elif tipo == "refletir_xy":
            # Reflexão pontual: inverte as duas coordenadas em relação ao ponto central
            xc = 2 * kw["cx"] - xc
            yc = 2 * kw["cy"] - yc

        return {**circ, "xc": int(xc), "yc": int(yc), "r": max(1, r)}