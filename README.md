# 🗡️ Roguelike-Game: Geração Procedural de Mapas

Um jogo roguelike 2D desenvolvido em Python utilizando **Pygame**, com foco em demonstração, exploração e transição entre diferentes algoritmos de **geração procedural de masmorras (dungeons)**.

---

## 🚀 Funcionalidades

- **Múltiplos Algoritmos de Geração Procedural**:
  - **Random Walk** (Caminhada Aleatória): Masmorras orgânicas e estilo caverna conectada.
  - **Cellular Automata** (Autômato Celular): Cavernas naturais com paredes suavizadas.
  - **BSP (Binary Space Partitioning)**: Salas retangulares conectadas por corredores tradicionais de masmorras.
  - **Gerador Híbrido**: Fusão de divisão de salas retangulares com autômatos celulares internos.
  - **Composição de Mapas**: Junção horizontal de diferentes algoritmos no mesmo nível (ex: metade BSP + metade Híbrido).
- **Movimentação e Colisão**:
  - Detecção precisa de colisão com paredes para o jogador.
  - Ponto de saída (portal) que gera um novo nível procedural ao ser alcançado.
- **Arquitetura Modular**:
  - Código limpo, desacoplado e pronto para expansão de novas entidades, inimigos, itens e mecânicas de combate.

---

## 🏛️ Arquitetura do Projeto

O projeto é estruturado em módulos independentes com responsabilidades bem definidas:

```text
Roguelike-Game/
├── collisions/             # Módulo de detecção de colisões
│   └── collision_manager.py# Verificação de colisão com paredes e gatilhos (saída)
├── entities/               # Entidades do jogo
│   └── player.py           # Classe do jogador (posição, movimentação, dimensões)
├── maps_generator/         # Algoritmos de geração procedural
│   ├── mapGenerator.py     # Classe base para matriz do mapa e costura de salas
│   ├── randomWalk.py       # Algoritmo de Random Walk
│   ├── cellularAutomata.py # Algoritmo de Autômatos Celulares
│   ├── bsp.py              # Algoritmo de Binary Space Partitioning
│   ├── hybridGenerator.py  # Algoritmo Híbrido (BSP + Autômatos)
│   └── map_service.py      # Serviço para criação e conversão de mapas para retângulos Pygame
├── rendering/              # Módulo de renderização gráfica
│   └── renderer.py         # Desenho de chão, paredes, saída e jogador na tela
├── config.py               # Constantes globais (dimensões de tela, tile size, cores, FPS)
├── main.py                 # Loop principal do jogo, captura de eventos e orquestração
└── README.md
```

---

## 🎮 Controles do Jogo

### 🏃 Movimentação
| Tecla | Ação |
| :---: | :--- |
| <kbd>W</kbd> | Mover para Cima |
| <kbd>A</kbd> | Mover para a Esquerda |
| <kbd>S</kbd> | Mover para Baixo |
| <kbd>D</kbd> | Mover para a Direita |

### 🗺️ Troca Rápida de Algoritmo de Mapa
| Tecla | Algoritmo Ativado |
| :---: | :--- |
| <kbd>R</kbd> | Random Walk |
| <kbd>C</kbd> | Cellular Automata |
| <kbd>B</kbd> | Binary Space Partitioning (BSP) |
| <kbd>M</kbd> | Gerador Híbrido |
| <kbd>F</kbd> | Mapa Combinado: BSP + Híbrido |
| <kbd>G</kbd> | Mapa Combinado: Híbrido + Cellular Automata |
| <kbd>H</kbd> | Mapa Combinado: Cellular Automata + Random Walk |

> **Objetivo do Nível:** Conduza o jogador (círculo vermelho) até a saída (círculo preto) para avançar de nível e gerar uma nova masmorra procedural!

---

## 📦 Pré-requisitos e Instalação

1. **Python**: Certifique-se de ter o Python 3.10+ instalado.
2. **Clone o repositório:**
   ```bash
   git clone https://github.com/JoaoPMagri/Roguelike-Game.git
   cd Roguelike-Game
   ```
3. **Instale a dependência (Pygame):**
   ```bash
   pip install pygame
   ```

---

## ▶️ Como Executar

Para iniciar o jogo, execute o arquivo `main.py`:

```bash
python main.py
```
*(ou caso use o launcher do Windows: `py main.py`)*