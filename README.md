# Trabalho Prático — Computação Gráfica

**Aluna:** Yasmin Cassemiro Viegas - 800989
**Professora:** Rosilane Mota


## Objetivo

O objetivo do trabalho é criar uma aplicação gráfica interativa de desenho 2D que implementa os principais algoritmos estudados na disciplina, sem uso de bibliotecas de desenho de alto nível. O usuário pode desenhar primitivas (retas, círculos e polígonos), selecioná-las, aplicar transformações geométricas, recortá-las por uma janela retangular e desenhar curvas paramétricas.


## Como Executar

### Pré-requisitos
- Python 3.8 ou superior
- pip

### Instalação das dependências

```bash
pip install -r requirements.txt
```

### Execução

```bash
python main.py
```

---

## TP1 — Primitivas, Transformações e Recorte

### Funcionalidades

#### Rasterização
- **Reta — DDA**: Incremento fracionário com arredondamento
- **Reta — Bresenham**: Aritmética inteira, selecionável via toolbar
- **Círculo — Bresenham**: Exploração de simetria de octantes

#### Recorte
- **Cohen-Sutherland**: Codificação por região com refinamento iterativo
- **Liang-Barsky**: Equação paramétrica com cálculo de intervalos u1/u2
- Recorte é **não-destrutivo**, ou seja, as primitivas originais são preservadas. O recorte é apenas um filtro aplicado na visualização

#### Transformações Geométricas 2D
- Translação
- Rotação (em torno do centro da tela)
- Escala (em torno do centro da tela)
- Reflexão em X (espelho horizontal)
- Reflexão em Y (espelho vertical)
- Reflexão em XY (reflexão pontual)

#### Interface
- Seleção de primitivas por região retangular
- Troca de cor de desenho
- Alternância entre algoritmos de reta e de recorte em tempo real
- Painel lateral com controles de transformação com valores livres

### Como Usar

- Desenhar reta: Selecionar modo **Reta** -> clicar no ponto inicial -> clicar no ponto final
- Desenhar círculo: Selecionar modo **Círculo** -> clicar no centro -> clicar para definir o raio
- Desenhar polígono: Selecionar modo **Polígono** -> clicar nos vértices -> botão **Finalizar Polígono** para fechar
- Selecionar objetos: Selecionar modo **Selecionar** -> arrastar um retângulo sobre os objetos
- Aplicar transformação: Selecionar objetos -> preencher valores no painel lateral -> clicar no botão da transformação
- Recortar: Selecionar modo **Recortar** -> arrastar um retângulo -> os objetos fora da janela são ocultados
- Remover recorte: Botão **Limpar Recorte**
- Trocar cor: Botão **Escolher** na toolbar
- Trocar algoritmo: Dropdowns **Alg. Reta** e **Alg. Recorte** na toolbar

---

## TP2 — Curvas Paramétricas

### Funcionalidades

#### Curvas
- **Bézier**: Aproximação polinomial via polinômios de Bernstein. A curva interpola apenas os pontos extremos, os pontos intermediários são de controle e atraem a curva sem ser tocados por ela
- **Hermite (Cúbica)**: Curva que interpola dois pontos extremos (P0 e P1) e utiliza dois pontos adicionais (R0 e R1) para controlar as tangentes. A tangente em P0 é T0 = R0 − P0, e em P1 é T1 = P1 − R1. A curva passa exatamente por P0 e P1; R0 e R1 definem a forma, mas não são tocados pela curva.

#### Interface
- Segunda toolbar exclusiva para curvas paramétricas, separada visualmente da toolbar do TP1
- Preview do polígono de controle em tempo real enquanto os pontos são clicados
- Finalização por botão ou duplo clique

### Como Usar

- Desenhar curva de Bézier: Selecionar modo **Bézier** -> clicar nos pontos de controle (mínimo 2) -> botão **Finalizar Curva** ou duplo clique
- Desenhar curva Hermite: Selecionar modo **Hermite** -> clicar exatamente 4 pontos na ordem: P0 (início), R0 (controle da tangente em P0), R1 (controle da tangente em P1) e P1 (fim) -> botão **Finalizar Curva** ou duplo clique
- Durante a construção, os pontos clicados aparecem marcados e conectados por uma linha tracejada azul mostrando o polígono de controle

### Referências dos algoritmos

- **Bézier**: Gist "Draw Bezier curves using Python and PyQt" -> https://gist.github.com/1274149/ca37e497b3f2a16c9d3ec4889ed63c80986e9dba
- **Hermite**: Adaptado de vedantyadu/Hermite-cubic-spline → https://github.com/vedantyadu/Hermite-cubic-spline

---

## Estrutura do Projeto

```
├── main.py              # Janela principal e painel de controle
├── paint.py             # Canvas de desenho — captura de eventos e renderização
├── requirements.txt     # Dependências do projeto
├── algoritmos/
│   ├── formas.py        # Estruturas de dados (Ponto, Reta, Polígono) e gerenciador
│   ├── rasterizacao.py  # Algoritmos DDA, Bresenham reta e Bresenham círculo
│   ├── recorte.py       # Algoritmos Cohen-Sutherland e Liang-Barsky
│   └── transform.py     # Transformações geométricas 2D
└── curvas/
    ├── bezier.py        # Curva de Bézier via polinômios de Bernstein
    └── hermite.py       # Curva de Hermite cúbica
```
