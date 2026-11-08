import os
import random
from typing import List
import pygame

from config import (
    TILE_SIZE,
    MAPTILES_PATH,
    SPRITE_SIZE,
    PLAYER_SPRITE_PATH,
    PLAYER_SPRITE_SIZE,
    MAP_PALETTES,
    COLOR_PLAYER,
)
from rendering.camera import Camera


class GameRenderer:
    # Colunas da spritesheet:
    # 0 = chão (floor), 1 = parede (wall), 2 = fundo (background), 3 = saída/porta (door)
    TILE_COLUMNS = {
        "floor": 0,
        "wall": 1,
        "background": 2,
        "door": 3,
    }

    # Linhas da spritesheet do jogador (PlayerModels.png):
    # 0 = baixo (down), 1 = direita (right), 2 = cima (up)
    PLAYER_DIRECTION_ROWS = {
        "down": 0,
        "right": 1,
        "up": 2,
    }
    PLAYER_FRAMES_COUNT = 4

    # A saída na spritesheet está orientada para o topo ("top" -> 0 graus).
    # pygame.transform.rotate gira no sentido anti-horário:
    # - top:    0°
    # - left:   90°
    # - bottom: 180°
    # - right:  270°
    DOOR_ROTATIONS = {
        "top": 0,
        "left": 90,
        "bottom": 180,
        "right": 270,
    }

    ROTATION_ANGLES = (0, 90, 180, 270)

    def __init__(self, surface: pygame.Surface, map_type: int = 0):
        self.surface = surface
        self.sprites = self._load_tileset()
        self.player_sprites = self._load_player_sprites()

        # Guarda a rotação orgânica de cada coordenada de tile {(tile_x, tile_y): angle}
        self.tile_rotations = {}
        self.current_level_key = None

        # =========================================================
        # CONTROLE DA TRANSIÇÃO
        # =========================================================

        # Guarda a decisão estática de cada tile:
        # {(x, y): algorithm}
        self.transition_mask = {}

        # Identifica qual transição está sendo exibida
        self.transition_key = None

    def _load_tileset(self) -> dict:
        """
        Carrega a spritesheet 4x4 (32x32 por tile):
        - Linhas (0..3): Random Walk, Cellular Automata, BSP, Hybrid
        - Colunas (0..3): floor, wall, background, door
        Pré-escala para TILE_SIZE e pré-rotaciona em 0°, 90°, 180° e 270°.
        """
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        tileset_full_path = os.path.join(base_dir, MAPTILES_PATH)
        sheet = pygame.image.load(tileset_full_path).convert()

        sprites = {}
        for algorithm in range(4):
            sprites[algorithm] = {}
            for tile_type, col in self.TILE_COLUMNS.items():
                rect = pygame.Rect(
                    col * SPRITE_SIZE,
                    algorithm * SPRITE_SIZE,
                    SPRITE_SIZE,
                    SPRITE_SIZE,
                )
                raw_tile = sheet.subsurface(rect)
                scaled_tile = pygame.transform.scale(
                    raw_tile,
                    (TILE_SIZE, TILE_SIZE),
                )

                sprites[algorithm][tile_type] = {
                    angle: pygame.transform.rotate(scaled_tile, angle)
                    for angle in self.ROTATION_ANGLES
                }

        return sprites

    def _load_player_sprites(self) -> dict:
        """
        Carrega a spritesheet do jogador (3 linhas x 4 colunas de 32x32):
        - Linha 0: baixo (down)
        - Linha 1: direita (right) -> espelhada horizontalmente para esquerda (left)
        - Linha 2: cima (up)
        """
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        player_full_path = os.path.join(base_dir, PLAYER_SPRITE_PATH)
        sheet = pygame.image.load(player_full_path).convert_alpha()

        player_sprites = {}
        for direction, row in self.PLAYER_DIRECTION_ROWS.items():
            frames = []
            for col in range(self.PLAYER_FRAMES_COUNT):
                rect = pygame.Rect(
                    col * SPRITE_SIZE,
                    row * SPRITE_SIZE,
                    SPRITE_SIZE,
                    SPRITE_SIZE,
                )
                raw_frame = sheet.subsurface(rect)
                scaled_frame = pygame.transform.scale(
                    raw_frame,
                    (PLAYER_SPRITE_SIZE, PLAYER_SPRITE_SIZE),
                )
                frames.append(scaled_frame)
            player_sprites[direction] = frames

        # Direção esquerda usa os sprites da direita espelhados horizontalmente
        player_sprites["left"] = [
            pygame.transform.flip(frame, True, False)
            for frame in player_sprites["right"]
        ]

        return player_sprites

    def _get_tile_rotation(self, tile_x: int, tile_y: int) -> int:
        """Retorna uma rotação aleatória fixa por coordenada de tile."""
        key = (tile_x, tile_y)
        if key not in self.tile_rotations:
            self.tile_rotations[key] = random.choice(self.ROTATION_ANGLES)
        return self.tile_rotations[key]

    def _get_split_boundary(self, camera: Camera, layout: str) -> int:
        """Retorna a linha divisória dos submapas em coordenadas do mundo."""
        if layout == "horizontal":
            tiles_x = camera.map_width // TILE_SIZE
            return (tiles_x // 2) * TILE_SIZE
        if layout == "vertical":
            tiles_y = camera.map_height // TILE_SIZE
            return (tiles_y // 2) * TILE_SIZE
        return 0

    def draw_map(
        self,
        floors: List[pygame.Rect],
        walls: List[pygame.Rect],
        camera: Camera,
        algorithm_a: int,
        algorithm_b: int = None,
        layout: str = None,
        reverse: bool = False
    ):
        viewport = camera.get_viewport_rect()

        floor_positions = {(rect.x, rect.y) for rect in floors}
        wall_positions = {(rect.x, rect.y) for rect in walls}

        start_x = max(0, (viewport.left // TILE_SIZE) * TILE_SIZE)
        end_x = min(camera.map_width, ((viewport.right // TILE_SIZE) + 1) * TILE_SIZE)
        start_y = max(0, (viewport.top // TILE_SIZE) * TILE_SIZE)
        end_y = min(camera.map_height, ((viewport.bottom // TILE_SIZE) + 1) * TILE_SIZE)

        for tile_y in range(start_y, end_y, TILE_SIZE):
            for tile_x in range(start_x, end_x, TILE_SIZE):
                tile_rect = pygame.Rect(tile_x, tile_y, TILE_SIZE, TILE_SIZE)

                if (tile_x, tile_y) in floor_positions:
                    tile_type = "floor"
                elif (tile_x, tile_y) in wall_positions:
                    tile_type = "wall"
                else:
                    tile_type = "background"

                algorithm = self._get_algorithm_for_rect(
                    tile_rect,
                    camera,
                    algorithm_a,
                    algorithm_b,
                    layout,
                    reverse,
                )

                angle = self._get_tile_rotation(tile_x, tile_y)
                sprite = self.sprites[algorithm][tile_type][angle]
                self.surface.blit(sprite, camera.apply(tile_rect))

    def _get_algorithm_for_rect(
        self,
        rect: pygame.Rect,
        camera: Camera,
        algorithm_a: int,
        algorithm_b: int,
        layout: str,
        reverse: bool
    ):
        """Decide qual algoritmo gerou um determinado retângulo de tile no mundo."""
        if algorithm_b is None:
            return algorithm_a

        first_algorithm = algorithm_b if reverse else algorithm_a
        second_algorithm = algorithm_a if reverse else algorithm_b

        if layout == "horizontal":
            boundary = self._get_split_boundary(camera, "horizontal")
            if rect.centerx < boundary:
                return first_algorithm
            return second_algorithm

        if layout == "vertical":
            boundary = self._get_split_boundary(camera, "vertical")
            if rect.centery < boundary:
                return first_algorithm
            return second_algorithm

        return algorithm_a

    def draw_door(self, door, level, camera: Camera):
        """Desenha a porta usando o sprite de saída rotacionado conforme a direção."""
        if door is None:
            return

        x, y = door["tile"]
        door_rect = pygame.Rect(x, y, TILE_SIZE, TILE_SIZE)

        if not camera.is_visible(door_rect):
            return

        if level["type"] == "pure":
            algorithm = level["algorithm"]
        else:
            algorithm = self._get_algorithm_for_rect(
                door_rect,
                camera,
                level["algorithm_a"],
                level["algorithm_b"],
                level["layout"],
                level["reverse"]
            )

        side = door.get("side", "top")
        angle = self.DOOR_ROTATIONS.get(side, 0)
        sprite = self.sprites[algorithm]["door"][angle]

        self.surface.blit(
            sprite,
            camera.apply(door_rect)
        )

    def draw_player(self, player, camera: Camera):
        screen_x, screen_y = camera.apply_point(player.x, player.y)
        direction_frames = self.player_sprites.get(
            player.direction,
            self.player_sprites["down"]
        )
        frame = direction_frames[player.frame_index % len(direction_frames)]
        sprite_rect = frame.get_rect(center=(screen_x, screen_y))
        self.surface.blit(frame, sprite_rect)

    def render_frame(
        self,
        floors: List[pygame.Rect],
        walls: List[pygame.Rect],
        player,
        exit_door,
        entrance_door,
        current_level_idx: int,
        level,
        camera: Camera,
        show_full_map: bool = False
    ):
        if current_level_idx != self.current_level_key:
            self.current_level_key = current_level_idx
            self.tile_rotations.clear()

        if show_full_map:
            self.draw_simplified_full_map(
                floors,
                walls,
                player,
                exit_door,
                entrance_door,
                level,
                camera
            )
            pygame.display.update()
            return

        # =========================================================
        # MAPA
        # =========================================================

        if level["type"] == "pure":
            # Mapa gerado por apenas um algoritmo
            self.draw_map(
                floors,
                walls,
                camera=camera,
                algorithm_a=level["algorithm"]
            )

        else:
            # Mapa intermediário: algoritmo A + algoritmo B
            self.draw_map(
                floors,
                walls,
                camera=camera,
                algorithm_a=level["algorithm_a"],
                algorithm_b=level["algorithm_b"],
                layout=level["layout"],
                reverse=level["reverse"]
            )

            self.draw_transition(
                floors,
                walls,
                camera=camera,
                algorithm_a=level["algorithm_a"],
                algorithm_b=level["algorithm_b"],
                layout=level["layout"],
                reverse=level["reverse"]
            )

        # =========================================================
        # PORTAS
        # =========================================================

        self.draw_door(entrance_door, level, camera)
        self.draw_door(exit_door, level, camera)

        # =========================================================
        # PLAYER
        # =========================================================

        self.draw_player(player, camera)

        pygame.display.update()

    def draw_transition(
        self,
        floors: List[pygame.Rect],
        walls: List[pygame.Rect],
        camera: Camera,
        algorithm_a: int,
        algorithm_b: int,
        layout: str,
        reverse: bool = False
    ):
        """
        Cria uma transição estática entre dois mapas em coordenadas do mundo,
        sorteando os tiles uma única vez por transição e mantendo o resultado.
        """
        transition_key = (
             self.current_level_key,
            algorithm_a,
            algorithm_b,
            layout,
            reverse
        )

        if transition_key != self.transition_key:
            self.transition_key = transition_key
            self.transition_mask.clear()

        if reverse:
            first_algorithm = algorithm_b
            second_algorithm = algorithm_a
        else:
            first_algorithm = algorithm_a
            second_algorithm = algorithm_b

        tile_types = {}

        for rect in floors:
            tile_types[(rect.x, rect.y)] = "floor"

        for rect in walls:
            tile_types[(rect.x, rect.y)] = "wall"

        viewport = camera.get_viewport_rect()

        def draw_tile(x, y, algorithm):
            world_rect = pygame.Rect(x, y, TILE_SIZE, TILE_SIZE)
            if not viewport.colliderect(world_rect):
                return

            tile_type = tile_types.get((x, y), "background")
            angle = self._get_tile_rotation(x, y)
            sprite = self.sprites[algorithm][tile_type][angle]

            self.surface.blit(
                sprite,
                camera.apply(world_rect)
            )

        width = camera.map_width
        height = camera.map_height

        # =========================================================
        # TRANSIÇÃO HORIZONTAL
        # =========================================================
        if layout == "horizontal":
            start = width / 3
            end = (width * 2) / 3

            x = start
            while x < end:
                progress = (x - start) / (end - start)
                progress = max(0.0, min(1.0, progress))
                chance = progress ** 2

                y = 0
                while y < height:
                    tile_x = int(x // TILE_SIZE) * TILE_SIZE
                    tile_y = int(y // TILE_SIZE) * TILE_SIZE
                    tile_position = (tile_x, tile_y)

                    if tile_position not in self.transition_mask:
                        if random.random() < chance:
                            self.transition_mask[tile_position] = second_algorithm
                        else:
                            self.transition_mask[tile_position] = first_algorithm

                    algorithm = self.transition_mask[tile_position]
                    draw_tile(tile_x, tile_y, algorithm)

                    y += TILE_SIZE

                x += TILE_SIZE

        # =========================================================
        # TRANSIÇÃO VERTICAL
        # =========================================================
        elif layout == "vertical":
            start = height / 3
            end = (height * 2) / 3

            y = start
            while y < end:
                progress = (y - start) / (end - start)
                progress = max(0.0, min(1.0, progress))
                chance = progress ** 2

                x = 0
                while x < width:
                    tile_x = int(x // TILE_SIZE) * TILE_SIZE
                    tile_y = int(y // TILE_SIZE) * TILE_SIZE
                    tile_position = (tile_x, tile_y)

                    if tile_position not in self.transition_mask:
                        if random.random() < chance:
                            self.transition_mask[tile_position] = second_algorithm
                        else:
                            self.transition_mask[tile_position] = first_algorithm

                    algorithm = self.transition_mask[tile_position]
                    draw_tile(tile_x, tile_y, algorithm)

                    x += TILE_SIZE

                y += TILE_SIZE

    def _scale_world_rect_to_screen(
        self,
        rect: pygame.Rect,
        camera: Camera
    ) -> pygame.Rect:
        """Converte um retângulo do mundo para a tela inteira (visão do mapa completo)."""
        screen_w = self.surface.get_width()
        screen_h = self.surface.get_height()
        map_w = camera.map_width
        map_h = camera.map_height

        x1 = round(rect.x * screen_w / map_w)
        y1 = round(rect.y * screen_h / map_h)
        x2 = round((rect.x + rect.width) * screen_w / map_w)
        y2 = round((rect.y + rect.height) * screen_h / map_h)

        return pygame.Rect(x1, y1, max(1, x2 - x1), max(1, y2 - y1))

    def draw_simplified_full_map(
        self,
        floors: List[pygame.Rect],
        walls: List[pygame.Rect],
        player,
        exit_door,
        entrance_door,
        level,
        camera: Camera
    ):
        """
        Renderiza o mapa completo ajustado à janela usando apenas as paletas de cores,
        sem sprites e sem recorte da câmera (ativado ao segurar TAB).
        """
        screen_w = self.surface.get_width()
        screen_h = self.surface.get_height()

        if level["type"] == "pure":
            algorithm_a = level["algorithm"]
            palette_a = MAP_PALETTES[algorithm_a]
            self.surface.fill(palette_a["background"])

            for rect in floors:
                pygame.draw.rect(
                    self.surface,
                    palette_a["floor"],
                    self._scale_world_rect_to_screen(rect, camera)
                )

            for rect in walls:
                pygame.draw.rect(
                    self.surface,
                    palette_a["wall"],
                    self._scale_world_rect_to_screen(rect, camera)
                )
        else:
            algorithm_a = level["algorithm_a"]
            algorithm_b = level["algorithm_b"]
            layout = level["layout"]
            reverse = level["reverse"]

            palette_a = MAP_PALETTES[algorithm_a]
            palette_b = MAP_PALETTES[algorithm_b]
            first_palette = palette_b if reverse else palette_a
            second_palette = palette_a if reverse else palette_b

            if layout == "horizontal":
                half_w = screen_w // 2
                pygame.draw.rect(
                    self.surface,
                    first_palette["background"],
                    pygame.Rect(0, 0, half_w, screen_h)
                )
                pygame.draw.rect(
                    self.surface,
                    second_palette["background"],
                    pygame.Rect(half_w, 0, screen_w - half_w, screen_h)
                )
            else:
                half_h = screen_h // 2
                pygame.draw.rect(
                    self.surface,
                    first_palette["background"],
                    pygame.Rect(0, 0, screen_w, half_h)
                )
                pygame.draw.rect(
                    self.surface,
                    second_palette["background"],
                    pygame.Rect(0, half_h, screen_w, screen_h - half_h)
                )

            for rect in floors:
                alg = self._get_algorithm_for_rect(
                    rect, camera, algorithm_a, algorithm_b, layout, reverse
                )
                pygame.draw.rect(
                    self.surface,
                    MAP_PALETTES[alg]["floor"],
                    self._scale_world_rect_to_screen(rect, camera)
                )

            for rect in walls:
                alg = self._get_algorithm_for_rect(
                    rect, camera, algorithm_a, algorithm_b, layout, reverse
                )
                pygame.draw.rect(
                    self.surface,
                    MAP_PALETTES[alg]["wall"],
                    self._scale_world_rect_to_screen(rect, camera)
                )

            # Aplica a máscara estática de transição com cores sólidas
            transition_key = (
                self.current_level_key,
                algorithm_a,
                algorithm_b,
                layout,
                reverse
            )
            if transition_key != self.transition_key:
                self.transition_key = transition_key
                self.transition_mask.clear()

            first_alg = algorithm_b if reverse else algorithm_a
            second_alg = algorithm_a if reverse else algorithm_b

            tile_types = {}
            for rect in floors:
                tile_types[(rect.x, rect.y)] = "floor"
            for rect in walls:
                tile_types[(rect.x, rect.y)] = "wall"

            width = camera.map_width
            height = camera.map_height

            if layout == "horizontal":
                start = width / 3
                end = (width * 2) / 3
                x = start
                while x < end:
                    progress = max(0.0, min(1.0, (x - start) / (end - start)))
                    chance = progress ** 2
                    y = 0
                    while y < height:
                        tile_x = int(x // TILE_SIZE) * TILE_SIZE
                        tile_y = int(y // TILE_SIZE) * TILE_SIZE
                        pos = (tile_x, tile_y)
                        if pos not in self.transition_mask:
                            self.transition_mask[pos] = (
                                second_alg if random.random() < chance else first_alg
                            )
                        alg = self.transition_mask[pos]
                        t_type = tile_types.get(pos, "background")
                        world_rect = pygame.Rect(tile_x, tile_y, TILE_SIZE, TILE_SIZE)
                        pygame.draw.rect(
                            self.surface,
                            MAP_PALETTES[alg][t_type],
                            self._scale_world_rect_to_screen(world_rect, camera)
                        )
                        y += TILE_SIZE
                    x += TILE_SIZE
            elif layout == "vertical":
                start = height / 3
                end = (height * 2) / 3
                y = start
                while y < end:
                    progress = max(0.0, min(1.0, (y - start) / (end - start)))
                    chance = progress ** 2
                    x = 0
                    while x < width:
                        tile_x = int(x // TILE_SIZE) * TILE_SIZE
                        tile_y = int(y // TILE_SIZE) * TILE_SIZE
                        pos = (tile_x, tile_y)
                        if pos not in self.transition_mask:
                            self.transition_mask[pos] = (
                                second_alg if random.random() < chance else first_alg
                            )
                        alg = self.transition_mask[pos]
                        t_type = tile_types.get(pos, "background")
                        world_rect = pygame.Rect(tile_x, tile_y, TILE_SIZE, TILE_SIZE)
                        pygame.draw.rect(
                            self.surface,
                            MAP_PALETTES[alg][t_type],
                            self._scale_world_rect_to_screen(world_rect, camera)
                        )
                        x += TILE_SIZE
                    y += TILE_SIZE

        # Portas (entrada e saída) com variação da cor da parede
        for door in (entrance_door, exit_door):
            if door is None:
                continue
            dx, dy = door["tile"]
            door_world_rect = pygame.Rect(dx, dy, TILE_SIZE, TILE_SIZE)
            if level["type"] == "pure":
                alg = level["algorithm"]
            else:
                alg = self._get_algorithm_for_rect(
                    door_world_rect,
                    camera,
                    level["algorithm_a"],
                    level["algorithm_b"],
                    level["layout"],
                    level["reverse"]
                )
            wall_color = MAP_PALETTES[alg]["wall"]
            door_color = tuple(min(255, c + 45) for c in wall_color)
            pygame.draw.rect(
                self.surface,
                door_color,
                self._scale_world_rect_to_screen(door_world_rect, camera)
            )

        # Jogador (círculo vermelho na posição correspondente no mapa completo)
        px = int(player.x * screen_w / camera.map_width)
        py = int(player.y * screen_h / camera.map_height)
        scale_factor = min(screen_w / camera.map_width, screen_h / camera.map_height)
        p_radius = max(5, int((TILE_SIZE * 0.35) * scale_factor))
        pygame.draw.circle(self.surface, COLOR_PLAYER, (px, py), p_radius)
