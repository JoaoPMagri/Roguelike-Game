# Roguelike-Game — Geração Procedural de Masmorras

Projeto de **Engenharia de Computação** desenvolvido em Python com **Pygame**, focado no estudo e implementação de algoritmos de **geração procedural de mapas**, composição de biomas, renderização 2D com câmera e *culling*, áudio dinâmico com *crossfade* e persistência de estado em JSON.

---

## 🏛️ Arquitetura do Projeto

O sistema segue uma arquitetura modular orientada a responsabilidades, desacoplando geração de mapas, lógica de colisão, renderização, persistência e orquestração:

```text
Roguelike-Game/
├── main.py                     # Orquestrador principal, game loop e máquina de estados (menu / playing / paused)
├── config.py                   # Constantes globais, paletas, opções de resolução/velocidade/volume e personagens
├── maps_generator/             # Núcleo de geração procedural
│   ├── mapGenerator.py         # Classe base da matriz do mapa e primitivas de costura
│   ├── randomWalk.py           # Caminhada Aleatória (cavernas orgânicas conectadas)
│   ├── cellularAutomata.py     # Autômatos Celulares (suavização iterativa de cavernas)
│   ├── bsp.py                  # Binary Space Partitioning (salas retangulares + corredores)
│   ├── hybridGenerator.py      # Gerador Híbrido (particionamento BSP + autômatos internos)
│   └── map_service.py          # Conversão para retângulos Pygame, portas, obstáculos e mapas intermediários
├── rendering/                  # Camada gráfica e interface
│   ├── renderer.py             # Renderização por viewport, sprites, filtros de efeito, minimapa e transições
│   ├── camera.py               # Câmera 2D com limites do mundo e cálculo de viewport
│   ├── hud.py                  # HUD com informações do nível e tema
│   └── menu.py                 # Menu inicial, seleção/detalhes de personagem, pause e configurações
├── entities/                   # Entidades e física básica
│   └── player.py               # Estado do jogador, animação de sprites e vetor de movimento
├── collisions/                 # Detecção e resolução de colisões
│   └── collision_manager.py    # Colisão AABB por eixo contra paredes, obstáculos e gatilhos de porta
├── persistence/                # Camada de persistência local
│   └── save_manager.py         # Leitura/escrita atômica de saves (slots) e configurações (JSON)
├── assets/                     # Spritesheets (personagens, tiles, obstáculos, efeitos) e trilhas sonoras (.mp3)
└── saves/                      # Arquivos persistidos localmente (settings.json e save_slot_*.json)
```

---

## 📚 Bibliotecas Utilizadas

- **`pygame`**: janela gráfica, loop de eventos, manipulação de superfícies/sprites (`Surface`, `Rect`, `transform.rotate`/`scale`) e subsistema de áudio (`pygame.mixer.music` e `pygame.mixer.Channel` / `Sound`).
- **Biblioteca Padrão Python**:
  - `random`: geração determinística/controlada via instâncias de `random.Random` com *seed* por nível.
  - `json` / `os`: serialização de estado e escrita atômica (`arquivo.tmp` + `os.replace`) para evitar corrupção de saves.
  - `sys`: encerramento limpo do processo.

---

## ⚙️ Algoritmos e Lógica Implementada

### 1. Geração Procedural Pura e Mapas Intermediários
- **Algoritmos Puros (`0`–`3`)**:
  - `0` — **Random Walk**: escavação estocástica em grade garantindo conectividade contínua.
  - `1` — **Cellular Automata**: inicialização aleatória seguida de regras de vizinhança para formar cavernas naturais.
  - `2` — **BSP (Binary Space Partitioning)**: divisão recursiva do espaço em folhas e conexão das salas por corredores.
  - `3` — **Gerador Híbrido**: combina particionamento espacial com preenchimento orgânico via autômatos celulares.
- **Mapas Intermediários (`intermediate`)**: unem dois algoritmos distintos no mesmo nível (divisão horizontal ou vertical), aplicando uma máscara de transição orgânica na fronteira para suavizar a mudança visual entre biomas.

### 2. Portas, Obstáculos e Efeitos Ambientais
- **Portas de Entrada e Saída**: posicionadas respeitando distância mínima entre si para evitar níveis triviais, permitindo avançar e retornar entre fases no histórico do nível.
- **Obstáculos e Navegabilidade**: gerados em áreas abertas (verificação de anel `5x5` de chão livre e espaçamento mínimo entre obstáculos), com *fallback* para áreas `3x3` em mapas mais fechados (como Random Walk), garantindo ao menos 1 obstáculo por mapa sem bloquear a passagem.
- **Efeitos de Área e Filtros**: cada obstáculo gera efeitos animados nas 8 posições adjacentes com rotação (`0°` a `315°`) e tamanhos variados. O contato do jogador ativa um filtro animado em tela correspondente ao algoritmo do obstáculo (Veneno, Radiação, Fogo ou Eletricidade) com tempo de permanência após sair da área.

### 3. Renderização, Minimapa (`TAB`) e Transição Deslizante
- **Viewport Culling**: `GameRenderer` desenha apenas os tiles e obstáculos visíveis no retângulo da câmera, mantendo o custo de renderização independente do tamanho total do mapa.
- **Exploração e Minimapa**: os tiles vistos pela câmera são registrados por nível; ao segurar `TAB`, o mapa completo explorado é exibido com marcação de portas (`X`), obstáculos (contorno circular) e posição do jogador.
- **Navegação entre Mapas no `TAB`**: ao pressionar a direção correspondente à entrada ou saída, uma transição deslizante em duas etapas conecta as duas portas por um corredor alinhado e, em seguida, centraliza o mapa de destino na tela.

### 4. Áudio Dinâmico com Crossfade
- Mapas puros reproduzem a trilha correspondente ao seu algoritmo via `pygame.mixer.music`.
- Mapas intermediários utilizam dois canais reservados (`pygame.mixer.Channel`) tocando simultaneamente as trilhas dos dois algoritmos envolvidos, ajustando o volume de cada canal em tempo real conforme a posição do jogador ao longo do eixo de divisão.

### 5. Persistência e Configurações
- **Saves (`save_slot_1.json`..`4`)**: armazenam personagem selecionado, histórico de níveis (*seeds*, tipos, layouts, portas, posição do jogador) e progresso explorado.
- **Configurações (`settings.json`)**: persistem resolução da janela, velocidade de processamento (multiplicador sobre a base de `120` FPS) e volume global (`0%` a `100%`).

---

## 🎮 Controles

| Tecla | Ação |
| :---: | :--- |
| <kbd>W</kbd> <kbd>A</kbd> <kbd>S</kbd> <kbd>D</kbd> | Movimentação do jogador |
| <kbd>TAB</kbd> (segurar) | Abrir minimapa explorado |
| <kbd>TAB</kbd> + <kbd>W</kbd>/<kbd>A</kbd>/<kbd>S</kbd>/<kbd>D</kbd> | Navegar visualmente entre mapas anteriores/posteriores pela porta correspondente |
| <kbd>ESC</kbd> | Abrir / fechar menu de pause |

---

## ▶️ Como Executar

1. Certifique-se de ter **Python 3.10+** instalado.
2. Instale a dependência:
   ```bash
   pip install pygame
   ```
3. Execute o jogo:
   ```bash
   python main.py
   ```
