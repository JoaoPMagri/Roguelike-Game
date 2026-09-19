# Configurações gerais da aplicação e constantes do jogo

# Dimensões da tela
WIDTH = 1280
HEIGHT = 720
FPS = 120

# Configurações do mapa e grid
TILE_SIZE = 32
MIN_LEAF_SIZE = 8

# Cores (R, G, B)
# Paletas por algoritmo
# 0 = Random Walk
# 1 = Cellular Automata
# 2 = BSP
# 3 = Hybrid

MAP_PALETTES = {
    0: {
        "background": (8, 51, 2),
        "wall": (18, 115, 4),
        "floor": (32, 207, 7),
    },

    1: {
        "background": (145, 108, 9),
        "wall": (207, 112, 11),
        "floor": (183, 194, 8),
    },

    2: {
        "background": (0, 0, 0),
        "wall": (61, 61, 61),
        "floor": (133, 133, 133),
    },

    3: {
        "background": (204, 30, 188),
        "wall": (15, 227, 208),
        "floor": (88, 8, 110),
    },
}

COLOR_PLAYER = (255, 0, 0)
COLOR_EXIT = (0, 0, 0)
COLOR_ENTRANCE = (255, 255, 255)
