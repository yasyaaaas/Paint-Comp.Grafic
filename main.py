"""
Aplicação Principal de Desenho para Computação Gráfica
"""

import sys

from PyQt5.QtWidgets import (
    QMainWindow, QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QDoubleSpinBox, QGroupBox,
    QComboBox, QColorDialog, QToolBar, QScrollArea
)
from PyQt5.QtCore import Qt

from paint import Paint

class JanelaPrincipal(QMainWindow):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Trabalho 1 e 2 - Computação Gráfica - Yasmin Viegas")
        self.setMinimumSize(900, 650)
        self.tela = Paint()
        self.setCentralWidget(self.tela)
        self._criar_toolbar()
        self._criar_painel_lateral()

    # ------------------------------------------------------------------
    # Toolbar
    # ------------------------------------------------------------------

    def _criar_toolbar(self):
        # --- Toolbar 1: primitivas clássicas, algoritmos e ações ---
        tb = QToolBar("Principal")
        tb.setMovable(False)
        tb.setToolButtonStyle(Qt.ToolButtonTextOnly)
        self.addToolBar(Qt.TopToolBarArea, tb)

        def sep(toolbar):
            s = QWidget(); s.setFixedWidth(8); toolbar.addWidget(s)

        def btn_toolbar(toolbar, label, fn):
            b = QPushButton(label); b.setFixedHeight(28); b.clicked.connect(fn)
            toolbar.addWidget(b); return b

        self._btns_modo = {}

        # Modos de desenho das primitivas clássicas
        tb.addWidget(QLabel("  Modo: "))
        for label, modo in [("Reta", "reta"), ("Círculo", "circulo"),
                             ("Polígono", "poligono"),
                             ("Selecionar", "selecionar"), ("Recortar", "recortar")]:
            b = QPushButton(label); b.setCheckable(True); b.setFixedHeight(28)
            b.clicked.connect(lambda _, m=modo: self._set_modo(m))
            tb.addWidget(b); self._btns_modo[modo] = b
        sep(tb)

        # Seletor de algoritmo de rasterização de retas
        tb.addWidget(QLabel("  Alg.Reta: "))
        combo_reta = QComboBox(); combo_reta.addItems(["Bresenham", "DDA"]); combo_reta.setFixedHeight(28)
        combo_reta.currentTextChanged.connect(
            lambda t: setattr(self.tela, 'algoritmo_reta', 'dda' if t == 'DDA' else 'bresenham'))
        tb.addWidget(combo_reta); sep(tb)

        # Seletor de algoritmo de recorte
        tb.addWidget(QLabel("  Alg.Recorte: "))
        combo_recorte = QComboBox(); combo_recorte.addItems(["Cohen-Sutherland", "Liang-Barsky"]); combo_recorte.setFixedHeight(28)
        combo_recorte.currentTextChanged.connect(
            lambda t: setattr(self.tela, 'algoritmo_recorte',
                              'cohen_sutherland' if 'Cohen' in t else 'liang_barsky'))
        tb.addWidget(combo_recorte); sep(tb)

        for label, fn in [("Finalizar Polígono", self.tela.finalizar_poligono),
                          ("Limpar Recorte",     self.tela.limpar_recorte),
                          ("Limpar Tudo",        self.tela.limpar_tela)]:
            btn_toolbar(tb, label, fn)

        # --- Toolbar 2: curvas paramétricas ---
        tb2 = QToolBar("Curvas Paramétricas")
        tb2.setMovable(False)
        tb2.setToolButtonStyle(Qt.ToolButtonTextOnly)
        self.addToolBar(Qt.TopToolBarArea, tb2)

        tb2.addWidget(QLabel("  Curvas Paramétricas: "))
        for label, modo in [("Bezier", "bezier"), ("Interpolada", "interpolada")]:
            b = QPushButton(label); b.setCheckable(True); b.setFixedHeight(28)
            b.clicked.connect(lambda _, m=modo: self._set_modo(m))
            tb2.addWidget(b); self._btns_modo[modo] = b
        sep(tb2)

        btn_toolbar(tb2, "Finalizar Curva", self.tela.finalizar_curva)

        self._set_modo("reta")

    # ------------------------------------------------------------------
    # Painel lateral — Transformações
    # ------------------------------------------------------------------

    def _criar_painel_lateral(self):
        dock = QWidget(); dock.setFixedWidth(230)
        dock.setStyleSheet("background:#f5f5f5;")
        outer = QVBoxLayout(dock); outer.setContentsMargins(4, 4, 4, 4)
        scroll = QScrollArea(); scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        outer.addWidget(scroll)
        inner = QWidget()
        layout = QVBoxLayout(inner); layout.setContentsMargins(4, 4, 4, 4); layout.setSpacing(6)
        scroll.setWidget(inner)

        def spinbox(prefixo, min_v, max_v, valor=None, step=None):
            sb = QDoubleSpinBox(); sb.setRange(min_v, max_v); sb.setPrefix(prefixo)
            if valor is not None: sb.setValue(valor)
            if step  is not None: sb.setSingleStep(step)
            return sb

        # Grupo Translação
        self.trans_dx = spinbox("dx ", -2000, 2000)
        self.trans_dy = spinbox("dy ", -2000, 2000)
        row_t = QWidget(); rh = QHBoxLayout(row_t); rh.setContentsMargins(0, 0, 0, 0)
        rh.addWidget(self.trans_dx); rh.addWidget(self.trans_dy)
        btn_t = QPushButton("Aplicar Translação"); btn_t.clicked.connect(self._transladar)
        gb = QGroupBox("Translação"); l = QVBoxLayout(gb); l.addWidget(row_t); l.addWidget(btn_t)
        layout.addWidget(gb)

        # Grupo Rotação
        self.rot_ang = spinbox("Ângulo ", -360, 360); self.rot_ang.setSuffix("°")
        btn_r = QPushButton("Aplicar Rotação"); btn_r.clicked.connect(self._rotacionar)
        gb2 = QGroupBox("Rotação"); l2 = QVBoxLayout(gb2); l2.addWidget(self.rot_ang); l2.addWidget(btn_r)
        layout.addWidget(gb2)

        # Grupo Escala
        self.esc_sx = spinbox("sx ", 0.01, 20, 1.0, 0.1)
        self.esc_sy = spinbox("sy ", 0.01, 20, 1.0, 0.1)
        row_e = QWidget(); re = QHBoxLayout(row_e); re.setContentsMargins(0, 0, 0, 0)
        re.addWidget(self.esc_sx); re.addWidget(self.esc_sy)
        btn_e = QPushButton("Aplicar Escala"); btn_e.clicked.connect(self._escalar)
        gb3 = QGroupBox("Escala"); l3 = QVBoxLayout(gb3); l3.addWidget(row_e); l3.addWidget(btn_e)
        layout.addWidget(gb3)

        # Grupo Reflexões
        gb4 = QGroupBox("Reflexões"); l4 = QVBoxLayout(gb4)
        for label, fn in [("Refletir X (Horizontal)", self._ref_x),
                          ("Refletir Y (Vertical)",   self._ref_y),
                          ("Refletir XY (Ponto)",     self._ref_xy)]:
            b = QPushButton(label); b.clicked.connect(fn); l4.addWidget(b)
        layout.addWidget(gb4)
        layout.addStretch()

        container = QWidget(); h = QHBoxLayout(container)
        h.setContentsMargins(0, 0, 0, 0); h.setSpacing(0)
        h.addWidget(self.tela); h.addWidget(dock)
        self.setCentralWidget(container)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _set_modo(self, modo):
        # Atualiza o modo ativo e desmarca os outros botões
        self.tela.modo_desenho = modo
        self.tela.ponto_inicio = None
        if modo != "poligono":
            self.tela.pontos_poligono = []
        for m, b in self._btns_modo.items():
            b.setChecked(m == modo)

    def _escolher_cor(self):
        cor = QColorDialog.getColor(self.tela.cor_foreground, self)
        if cor.isValid():
            self.tela.cor_foreground = cor
            self.tela.rasterizador.definir_cor((cor.red(), cor.green(), cor.blue()))
            self.lbl_cor.setStyleSheet(f"background:{cor.name()}; border:1px solid #888;")

    def _cx_cy(self):
        # Centro da tela
        return self.tela.width() / 2, self.tela.height() / 2

    def _transladar(self):
        self.tela.transformar_selecionados("transladar", dx=self.trans_dx.value(), dy=self.trans_dy.value())

    def _rotacionar(self):
        cx, cy = self._cx_cy()
        self.tela.transformar_selecionados("rotacionar", cx=cx, cy=cy, angulo=self.rot_ang.value())

    def _escalar(self):
        cx, cy = self._cx_cy()
        self.tela.transformar_selecionados("escalar", cx=cx, cy=cy, sx=self.esc_sx.value(), sy=self.esc_sy.value())

    def _ref_x(self):
        self.tela.transformar_selecionados("refletir_x", eixo_y=self.tela.height() / 2)

    def _ref_y(self):
        self.tela.transformar_selecionados("refletir_y", eixo_x=self.tela.width() / 2)

    def _ref_xy(self):
        cx, cy = self._cx_cy()
        self.tela.transformar_selecionados("refletir_xy", cx=cx, cy=cy)

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    janela = JanelaPrincipal()
    janela.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()