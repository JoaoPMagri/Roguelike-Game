# Configurações gerais da aplicação e constantes do jogo

# Dimensões da tela e opções pré-definidas de configurações
WIDTH = 1280
HEIGHT = 720
FPS = 120

RESOLUTION_OPTIONS = [
    (854, 480),
    (1024, 576),
    (1280, 720),
    (1600, 900),
    (1920, 1080),
]

FPS_OPTIONS = [30, 60, 120, 144, 240]

# Configurações do mapa e grid
TILE_SIZE = 224
MAP_WIDTH = 60
MAP_HEIGHT = 36
MIN_LEAF_SIZE = 8

# Configurações do jogador (proporcionais ao tamanho do tile)
PLAYER_SPEED = TILE_SIZE * 0.025
PLAYER_SPRITE_PATH = "assets/PlayerSprites/ElectricCiborgue.png"
PLAYER_SPRITE_SIZE = int(TILE_SIZE * 0.35)
PLAYER_HITBOX_WIDTH = int(PLAYER_SPRITE_SIZE * 0.68)
PLAYER_HITBOX_HEIGHT = int(PLAYER_SPRITE_SIZE * 0.94)
PLAYER_RADIUS = PLAYER_HITBOX_WIDTH / 2
PLAYER_ANIMATION_COOLDOWN = 80

CHARACTER_OPTIONS = [
    {
        "id": "electric_cyborg",
        "name": "Electric Ciborgue",
        "sprite_path": "assets/PlayerSprites/ElectricCiborgue.png",
        "accent_color": (15, 227, 208),
        "theme_map": 3,  # Híbrido
    },
    {
        "id": "fire_knight",
        "name": "Fire Knight",
        "sprite_path": "assets/PlayerSprites/FireKnight.png",
        "accent_color": (255, 110, 40),
        "theme_map": 2,  # BSP
    },
    {
        "id": "poison_druid",
        "name": "Poison Druid",
        "sprite_path": "assets/PlayerSprites/PoisonDruid.png",
        "accent_color": (32, 207, 7),
        "theme_map": 0,  # Random Walk
    },
    {
        "id": "rad_survivor",
        "name": "Rad Survivor",
        "sprite_path": "assets/PlayerSprites/RadSurvivor.png",
        "accent_color": (195, 215, 25),
        "theme_map": 1,  # Cellular Automata
    },
]

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
        "background": (0, 87, 79),
        "wall": (88, 8, 110),
        "floor": (16, 212, 111),
    },
}

COLOR_PLAYER = (255, 0, 0)
COLOR_EXIT = (0, 0, 0)
COLOR_ENTRANCE = (255, 255, 255)
