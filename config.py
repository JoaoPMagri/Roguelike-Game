# Configurações gerais da aplicação e constantes do jogo

# Dimensões da tela e opções pré-definidas de configurações
WIDTH = 1280
HEIGHT = 720
FPS = 120

RESOLUTION_OPTIONS = [
    (640, 360),
    (854, 480),
    (960, 540),
    (1024, 576),
    (1152, 648),
    (1280, 720),
    (1366, 768),
    (1440, 810),
    (1600, 900),
    (1760, 990),
    (1920, 1080),
]

PROCESSING_SPEED_OPTIONS = [0.25, 0.3, 0.5, 0.75, 1.0, 1.25, 1.5, 2.0, 2.5, 3.0]

# Configurações do mapa e grid
TILE_SIZE = 180
MAP_WIDTH = 60
MAP_HEIGHT = 36
MIN_LEAF_SIZE = 8

# Configurações do jogador (proporcionais ao tamanho do tile)
PLAYER_SPEED = TILE_SIZE * 0.025
PLAYER_SPRITE_PATH = "assets/PlayerSprites/ElectricCiborgue.png"
PLAYER_SPRITE_SIZE = int(TILE_SIZE * 0.4)
PLAYER_HITBOX_WIDTH = int(PLAYER_SPRITE_SIZE * 0.68)
PLAYER_HITBOX_HEIGHT = int(PLAYER_SPRITE_SIZE * 0.94)
PLAYER_RADIUS = PLAYER_HITBOX_WIDTH / 2
PLAYER_ANIMATION_COOLDOWN = 80

CHARACTER_OPTIONS = [
    {
        "id": "electric_cyborg",
        "name": "Electric Ciborgue",
        "title": "Ciborgue — A Última Esperança",
        "quote": "Disposto a sacrificar parte de sua humanidade para proteger o pouco que restou. Se não pode vencê-los, torne-se um deles.",
        "lore": "Em um futuro distante, onde a humanidade foi dominada por robôs e pela alta tecnologia, o Ciborgue utiliza sua parte mecânica para enfrentá-los de igual para igual. Entretanto, o que realmente o diferencia é sua humanidade: sua capacidade de adaptação o coloca à frente de seus oponentes. Para os poucos humanos que ainda restam, ele se tornou um símbolo de esperança.",
        "affinity": "Eletricidade",
        "weakness": "Radiação",
        "sprite_path": "assets/PlayerSprites/ElectricCiborgue.png",
        "accent_color": (15, 227, 208),
        "theme_map": 3,  # Híbrido
    },
    {
        "id": "fire_knight",
        "name": "Fire Knight",
        "title": "Cavaleiro — Último Guardião",
        "quote": "Dizem que, por baixo da armadura, existe um corpo coberto de queimaduras. Verdade ou não, uma coisa é certa: ele está acostumado a lidar com o fogo.",
        "lore": "Em um castelo em ruínas, cercado por chamas e lava, vaga um forte cavaleiro de um reino que já não existe. Especialista em combate corpo a corpo, mesmo sem ter a quem servir, continua lutando em nome da honra de seu reino e na esperança de um dia vingá-lo.",
        "affinity": "Fogo",
        "weakness": "Eletricidade",
        "sprite_path": "assets/PlayerSprites/FireKnight.png",
        "accent_color": (255, 110, 40),
        "theme_map": 2,  # BSP
    },
    {
        "id": "poison_druid",
        "name": "Poison Druid",
        "title": "Druida — Guardiã da Floresta",
        "quote": "Nascida e criada pela floresta, luta para proteger aquela que sempre a protegeu.",
        "lore": "Em um bosque encantado, habitado por criaturas mágicas e repleto de toxinas fatais, a Druida utiliza a magia arcana e sua conexão com a natureza para combater qualquer um que ouse ameaçar seu lar. Para ela, a floresta não é apenas seu lar, mas parte de quem ela é.",
        "affinity": "Veneno",
        "weakness": "Fogo",
        "sprite_path": "assets/PlayerSprites/PoisonDruid.png",
        "accent_color": (32, 207, 7),
        "theme_map": 0,  # Random Walk
    },
    {
        "id": "rad_survivor",
        "name": "Rad Survivor",
        "title": "Sobrevivente — Lei da Sobrevivência",
        "quote": "O fim da civilização também representa o fim do comportamento civilizado. Para sobreviver, é necessário atirar primeiro e perguntar depois.",
        "lore": "Após uma guerra nuclear, a vida na Terra nunca mais foi a mesma. Em meio aos destroços e à radiação, vaga uma figura misteriosa e encapuzada, munida de armas e explosivos improvisados. Em um mundo repleto de criaturas mutantes, poucos são capazes de representar uma ameaça tão grande quanto ele. E menos ainda sobreviveram para contar a história.",
        "affinity": "Radiação",
        "weakness": "Veneno",
        "sprite_path": "assets/PlayerSprites/RadSurvivor.png",
        "accent_color": (195, 215, 25),
        "theme_map": 1,  # Cellular Automata
    },
]

# Distância mínima desejada entre entrada e saída de um mesmo mapa.
MIN_DOOR_DISTANCE_TILES = 25

# Configurações do Tileset (4x4 sprites de 64x64 pixels) e sprites de personagem (32x32)
MAPTILES_PATH = "assets/MapTiles.png"
OBSTACLES_PATH = "assets/Obstacles.png"
OBSTACLE_SPAWN_CHANCE = 0.02
EFFECT_ANIMATION_COOLDOWN = 500
EFFECT_DURATION_MS = 3000
OBSTACLE_EFFECT_FILTERS = {
    0: (190, 50, 210, 105),   # Roxo / Rosa (Veneno)
    1: (120, 220, 40, 105),   # Verde / Amarelo (Radiação)
    2: (240, 95, 25, 105),    # Vermelho / Laranja (Fogo)
    3: (110, 200, 255, 105),  # Azul / Branco (Eletricidade)
}
MAP_SPRITE_SIZE = 64
SPRITE_SIZE = 32

# Cores (R, G, B)
# Paletas por algoritmo
# 0 = Random Walk
# 1 = Cellular Automata
# 2 = BSP
# 3 = Hybrid

MAP_PALETTES = {
    0: {
        "background": (222, 216, 181),
        "wall": (64, 91, 56),
        "floor": (166, 183, 124),
    },

    1: {
        "background": (201, 173, 120),
        "wall": (101, 69, 47),
        "floor": (224, 197, 140),
    },

    2: {
        "background": (219, 204, 174),
        "wall": (69, 67, 74),
        "floor": (169, 151, 137),
    },

    3: {
        "background": (199, 221, 227),
        "wall": (41, 70, 93),
        "floor": (120, 191, 194),
    },
}

COLOR_PLAYER = (255, 0, 0)
