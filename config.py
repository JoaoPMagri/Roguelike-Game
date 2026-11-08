# Configurações gerais da aplicação e constantes do jogo

# Dimensões da tela
WIDTH = 1280
HEIGHT = 720
FPS = 120

# Configurações do mapa e grid
TILE_SIZE = 224
MAP_WIDTH = 60
MAP_HEIGHT = 36
MIN_LEAF_SIZE = 8

# Configurações do jogador (proporcionais ao tamanho do tile)
PLAYER_SPEED = TILE_SIZE * 0.025
PLAYER_SPRITE_PATH = "assets/PlayerModels.png"
PLAYER_SPRITE_SIZE = int(TILE_SIZE * 0.35)
PLAYER_HITBOX_WIDTH = int(PLAYER_SPRITE_SIZE * 0.68)
PLAYER_HITBOX_HEIGHT = int(PLAYER_SPRITE_SIZE * 0.94)
PLAYER_RADIUS = PLAYER_HITBOX_WIDTH / 2
PLAYER_ANIMATION_COOLDOWN = 80

# Distância mínima desejada entre entrada e saída de um mesmo mapa.
MIN_DOOR_DISTANCE_TILES = 25

# Configurações do Tileset (4x4 sprites de 32x32 pixels)
MAPTILES_PATH = "assets/MapTiles.png"
SPRITE_SIZE = 32

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
