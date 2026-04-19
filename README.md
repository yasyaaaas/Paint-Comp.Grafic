# Trabalho Prático — Computação Gráfica
**Implementação de Algoritmos — Unidade 1**

**Aluna:** Yasmin Cassemiro Viegas - 800989  
**Professora:** Rosilane Mota  

---

## Objetivo

O objetivo do trabalho é criar uma aplicação gráfica interativa de desenho 2D que implementa os principais algoritmos estudados na disciplina, sem uso de bibliotecas de desenho de alto nível. O usuário pode desenhar primitivas (retas, círculos e polígonos), selecioná-las, aplicar transformações geométricas e recortá-las por uma janela retangular.

---

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

## Funcionalidades

### Rasterização
- **Reta — DDA**:Iincremento fracionário com arredondamento
- **Reta — Bresenham**: Aritmética inteira, selecionável via toolbar
- **Círculo — Bresenham**: Exploração de simetria de octantes

### Recorte
- **Cohen-Sutherland**: Codificação por região com refinamento iterativo
- **Liang-Barsky**: Equação paramétrica com cálculo de intervalos u1/u2
- Recorte é **não-destrutivo**, ou seja as primitivas originais são preservadas. O recorte é apenas um filtro aplicado na visualização

### Transformações Geométricas 2D
- Translação
- Rotação (em torno do centro da tela)
- Escala (em torno do centro da tela)
- Reflexão em X (espelho horizontal)
- Reflexão em Y (espelho vertical)
- Reflexão em XY (reflexão pontual)

### Interface
- Seleção de primitivas por região retangular
- Troca de cor de desenho
- Alternância entre algoritmos de reta e de recorte em tempo real
- Painel lateral com controles de transformação com valores livres

---

## Como Usar

- Desenhar reta: Selecionar modo **Reta** ->  clicar no ponto inicial ->  clicar no ponto final
- Desenhar círculo: Selecionar modo **Círculo** -> clicar no centro -> clicar para definir o raio
- Desenhar polígono: Selecionar modo **Polígono** -> clicar nos vértices -> botão **Finalizar Polígono** para fechar
- Selecionar objetos: Selecionar modo **Selecionar** -> arrastar um retângulo sobre os objetos
- Aplicar transformação: Selecionar objetos -> preencher valores no painel lateral -> clicar no botão da transformação
- Recortar: Selecionar modo **Recortar** -> arrastar um retângulo -> os objetos fora da janela são ocultados
- Remover recorte: Botão **Limpar Recorte**
- Trocar cor: Botão **Escolher** na toolbar
- Trocar algoritmo: Dropdowns **Alg. Reta** e **Alg. Recorte** na toolbar

---

## Estrutura do Projeto

```
├── main.py              # Janela principal e painel de controle
├── paint.py             # Canvas de desenho — captura de eventos e renderização
├── requirements.txt     # Dependências do projeto
└── algoritmos/
    ├── formas.py        # Estruturas de dados (Ponto, Reta, Polígono) e gerenciador
    ├── rasterizacao.py  # Algoritmos DDA, Bresenham reta e Bresenham círculo
    ├── recorte.py       # Algoritmos Cohen-Sutherland e Liang-Barsky
    └── transform.py     # Transformações geométricas 2D
```