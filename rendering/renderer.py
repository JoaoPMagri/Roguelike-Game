import os
import random
from typing import List
import pygame

from config import (
    TILE_SIZE,
    MAPTILES_PATH,
    OBSTACLES_PATH,
    EFFECT_ANIMATION_COOLDOWN,
    OBSTACLE_EFFECT_FILTERS,
    MAP_SPRITE_SIZE,
    SPRITE_SIZE,
    PLAYER_SPRITE_PATH,
    PLAYER_SPRITE_SIZE,
    MAP_PALETTES,
    COLOR_PLAYER,
)
from rendering.camera import Camera
from rendering.hud import HUD
from persistence import get_resource_path


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

    def __init__(self, surface: pygame.Surface, map_type: int = 0):
        self.surface = surface
        self.sprites = self._load_tileset()
        self.obstacle_sprites = self._load_obstacle_sprites()
        self.player_sprites = self._load_player_sprites()
        self.player_theme_map = 0
        self.hud = HUD(self.surface)

        self.current_level_key = None

        # Guarda os tiles já renderizados (explorados) por nível:
        # {level_idx: set((tile_x, tile_y))}
        self.explored_tiles_by_level = {}

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
        Carrega a spritesheet 4x4 (64x64 por tile):
        - Linhas (0..3): Random Walk, Cellular Automata, BSP, Hybrid
        - Colunas (0..3): floor, wall, background, door
        Escala cada tile para TILE_SIZE mantendo a orientação original.
        """
        tileset_full_path = get_resource_path(MAPTILES_PATH)
        sheet = pygame.image.load(tileset_full_path).convert()

        sprites = {}
        for algorithm in range(4):
            sprites[algorithm] = {}
            for tile_type, col in self.TILE_COLUMNS.items():
                rect = pygame.Rect(
                    col * MAP_SPRITE_SIZE,
                    algorithm * MAP_SPRITE_SIZE,
                    MAP_SPRITE_SIZE,
                    MAP_SPRITE_SIZE,
                )
                raw_tile = sheet.subsurface(rect)
                scaled_tile = pygame.transform.scale(
                    raw_tile,
                    (TILE_SIZE, TILE_SIZE),
                )
                if tile_type == "door":
                    sprites[algorithm][tile_type] = {
                        angle: pygame.transform.rotate(scaled_tile, angle)
                        for angle in self.DOOR_ROTATIONS.values()
                    }
                else:
                    sprites[algorithm][tile_type] = scaled_tile

        return sprites

    def _load_obstacle_sprites(self) -> dict:
        """
        Carrega os sprites de obstáculos e efeitos (3 colunas x 4 linhas de 64x64):
        - Coluna 0: obstáculo sólido
        - Colunas 1 e 2: frames animados do efeito ao redor do obstáculo
        - Linhas (0..3): Random Walk, Cellular Automata, BSP, Hybrid
        """
        obstacles_full_path = get_resource_path(OBSTACLES_PATH)
        sheet = pygame.image.load(obstacles_full_path).convert_alpha()

        obstacle_sprites = {}
        for algorithm in range(4):
            row_sprites = []
            for col in range(3):
                rect = pygame.Rect(
                    col * MAP_SPRITE_SIZE,
                    algorithm * MAP_SPRITE_SIZE,
                    MAP_SPRITE_SIZE,
                    MAP_SPRITE_SIZE,
                )
                raw_sprite = sheet.subsurface(rect)
                row_sprites.append(
                    pygame.transform.scale(raw_sprite, (TILE_SIZE, TILE_SIZE))
                )
            obstacle_sprites[algorithm] = {
                "obstacle": row_sprites[0],
                "effects": [row_sprites[1], row_sprites[2]],
            }

        return obstacle_sprites

    def _load_player_sprites(self, sprite_path: str = PLAYER_SPRITE_PATH) -> dict:
        """
        Carrega a spritesheet do jogador (3 linhas x 4 colunas de 32x32):
        - Linha 0: baixo (down)
        - Linha 1: direita (right) -> espelhada horizontalmente para esquerda (left)
        - Linha 2: cima (up)
        """
        player_full_path = get_resource_path(sprite_path)
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

    def set_player_sprite(self, sprite_path: str):
        """Atualiza os sprites do jogador com base no personagem selecionado."""
        self.player_sprites = self._load_player_sprites(sprite_path)

    def set_player_theme(self, theme_map: int):
        """Define a paleta de tema do personagem para o mapa desenhado (TAB)."""
        if theme_map in MAP_PALETTES:
            self.player_theme_map = theme_map

    def set_surface(self, surface: pygame.Surface):
        """Atualiza a superfície de renderização quando o tamanho da janela muda."""
        self.surface = surface
        self.hud.surface = surface

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

        explored = self.explored_tiles_by_level.setdefault(
            self.current_level_key, set()
        )

        for tile_y in range(start_y, end_y, TILE_SIZE):
            for tile_x in range(start_x, end_x, TILE_SIZE):
                explored.add((tile_x, tile_y))
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

                sprite = self.sprites[algorithm][tile_type]
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

    def get_algorithm_at_rect(self, rect: pygame.Rect, camera: Camera, level) -> int:
        """Retorna o algoritmo (0..3) correspondente à posição do retângulo no mundo."""
        if level["type"] == "pure":
            return level["algorithm"]

        pos = (rect.x, rect.y)
        if pos in self.transition_mask:
            return self.transition_mask[pos]

        return self._get_algorithm_for_rect(
            rect,
            camera,
            level["algorithm_a"],
            level["algorithm_b"],
            level["layout"],
            level["reverse"],
        )

    def draw_obstacles(self, obstacles: List[pygame.Rect], camera: Camera, level):
        """Desenha os obstáculos visíveis na câmera usando o sprite do ambiente."""
        viewport = camera.get_viewport_rect()
        for rect in obstacles:
            if not viewport.colliderect(rect):
                continue

            algorithm = self.get_algorithm_at_rect(rect, camera, level)
            sprite = self.obstacle_sprites[algorithm]["obstacle"]
            self.surface.blit(sprite, camera.apply(rect))

    def draw_obstacle_effects(self, obstacle_effects: List[dict], camera: Camera, level):
        """Desenha os efeitos animados ao redor dos obstáculos alternando entre as colunas 1 e 2."""
        viewport = camera.get_viewport_rect()
        toggle = (pygame.time.get_ticks() // EFFECT_ANIMATION_COOLDOWN) % 2

        for effect in obstacle_effects:
            rect = effect["rect"]
            if not viewport.colliderect(rect):
                continue

            algo_rect = effect.get("obstacle_rect", rect)
            algorithm = self.get_algorithm_at_rect(algo_rect, camera, level)
            frame_idx = (effect["initial_frame"] + toggle) % 2
            sprite = self.obstacle_sprites[algorithm]["effects"][frame_idx]
            if sprite.get_size() != rect.size:
                sprite = pygame.transform.scale(sprite, rect.size)
            angle = effect.get("angle", 0)
            if angle != 0:
                sprite = pygame.transform.rotate(sprite, angle)
            screen_rect = camera.apply(rect)
            blit_rect = sprite.get_rect(center=screen_rect.center)
            self.surface.blit(sprite, blit_rect)

    def draw_screen_filter(self, effect_algorithm: int):
        """Aplica um filtro animado na tela via código conforme o efeito ativo."""
        if effect_algorithm is None:
            return
        color = OBSTACLE_EFFECT_FILTERS.get(effect_algorithm)
        if color is None:
            return

        w, h = self.surface.get_size()
        overlay = pygame.Surface((w, h), pygame.SRCALPHA)
        overlay.fill(color)

        t = pygame.time.get_ticks()

        if effect_algorithm == 0:
            # Veneno (Roxo / Rosa): bolhas subindo pelas bordas
            for i in range(24):
                bx = int(((i * 97 + 31) % 100) / 100 * w)
                # Concentra mais nas laterais para manter o centro legível
                if w * 0.25 < bx < w * 0.75:
                    bx = (bx % int(w * 0.25)) if i % 2 == 0 else w - (bx % int(w * 0.25))
                speed = 0.05 + (i % 4) * 0.02
                by = int((h - ((t * speed + i * 73) % (h + 60))) + 30)
                radius = 10 + (i % 5) * 5
                bubble_color = (235, 110, 245, 165) if i % 2 == 0 else (160, 40, 200, 175)
                pygame.draw.circle(overlay, bubble_color, (bx, by), radius)
                pygame.draw.circle(overlay, (255, 200, 255, 200), (bx - radius // 3, by - radius // 3), max(3, radius // 4))

        elif effect_algorithm == 1:
            # Radiação (Verde / Amarelo): linhas de estática e partículas pulsantes
            pulse = 24 + int(abs((t % 600) - 300) / 300 * 30)
            pygame.draw.rect(overlay, (180, 245, 40, pulse + 65), pygame.Rect(0, 0, w, h), width=22)
            step = (t // 90) % 10
            for i in range(22):
                ly = ((i * 67 + step * 43) % h)
                lx = ((i * 131 + step * 71) % max(1, w - 160))
                lw = 65 + (i % 4) * 45
                line_color = (230, 255, 80, 170) if i % 2 == 0 else (90, 220, 40, 160)
                pygame.draw.line(overlay, line_color, (lx, ly), (lx + lw, ly), 3)

        elif effect_algorithm == 2:
            # Fogo (Vermelho / Laranja): brilho inferior e brasas subindo
            glow_h = max(90, h // 4)
            glow_rect = pygame.Rect(0, h - glow_h, w, glow_h)
            pygame.draw.rect(overlay, (255, 110, 20, 125), glow_rect)
            for i in range(30):
                base_x = int(((i * 89 + 17) % 100) / 100 * w)
                sway = int(22 * ((t // 120 + i) % 3 - 1))
                bx = max(4, min(w - 4, base_x + sway))
                speed = 0.08 + (i % 5) * 0.025
                progress = ((t * speed + i * 53) % h) / h
                by = int(h - progress * h)
                radius = max(4, int((1.0 - progress) * 12) + 3)
                ember_color = (255, 190, 50, 220) if i % 2 == 0 else (255, 80, 20, 200)
                pygame.draw.circle(overlay, ember_color, (bx, by), radius)

        elif effect_algorithm == 3:
            # Eletricidade (Azul / Branco): raios em zigue-zague nas bordas
            flash_seed = t // 70
            rng_fx = random.Random(flash_seed)
            for _ in range(8):
                side = rng_fx.randint(0, 3)
                if side == 0:
                    sx, sy = rng_fx.randint(0, w), 0
                    dx, dy = rng_fx.randint(-38, 38), rng_fx.randint(45, 75)
                elif side == 1:
                    sx, sy = rng_fx.randint(0, w), h
                    dx, dy = rng_fx.randint(-38, 38), -rng_fx.randint(45, 75)
                elif side == 2:
                    sx, sy = 0, rng_fx.randint(0, h)
                    dx, dy = rng_fx.randint(45, 75), rng_fx.randint(-38, 38)
                else:
                    sx, sy = w, rng_fx.randint(0, h)
                    dx, dy = -rng_fx.randint(45, 75), rng_fx.randint(-38, 38)

                points = [(sx, sy)]
                cx, cy = sx, sy
                for _seg in range(4):
                    cx += dx + rng_fx.randint(-28, 28)
                    cy += dy + rng_fx.randint(-28, 28)
                    points.append((cx, cy))

                pygame.draw.lines(overlay, (140, 220, 255, 215), False, points, 6)
                pygame.draw.lines(overlay, (255, 255, 255, 250), False, points, 3)

        self.surface.blit(overlay, (0, 0))

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
        show_full_map: bool = False,
        flip_display: bool = True,
        obstacles: List[pygame.Rect] = None,
        obstacle_effects: List[dict] = None,
        active_screen_effect: int = None,
        draw_player_marker: bool = True
    ):
        if current_level_idx != self.current_level_key:
            self.current_level_key = current_level_idx

        if show_full_map:
            self.draw_simplified_full_map(
                floors,
                walls,
                player,
                exit_door,
                entrance_door,
                level,
                camera,
                draw_player_marker=draw_player_marker,
                obstacles=obstacles,
            )
            if flip_display:
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
        # PORTAS E OBSTÁCULOS
        # =========================================================

        self.draw_door(entrance_door, level, camera)
        self.draw_door(exit_door, level, camera)
        if obstacle_effects:
            self.draw_obstacle_effects(obstacle_effects, camera, level)
        if obstacles:
            self.draw_obstacles(obstacles, camera, level)

        # =========================================================
        # PLAYER
        # =========================================================

        self.draw_player(player, camera)

        # =========================================================
        # FILTRO DE EFEITO NA TELA
        # =========================================================

        self.draw_screen_filter(active_screen_effect)

        # =========================================================
        # HUD
        # =========================================================

        self.hud.draw(current_level_idx, level, player)

        if flip_display:
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
            sprite = self.sprites[algorithm][tile_type]

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
        camera: Camera,
        offset: tuple[int, int] = (0, 0)
    ) -> pygame.Rect:
        """Converte um retângulo do mundo para a tela inteira (visão do mapa completo)."""
        screen_w = self.surface.get_width()
        screen_h = self.surface.get_height()
        map_w = camera.map_width
        map_h = camera.map_height

        x1 = round(rect.x * screen_w / map_w) + offset[0]
        y1 = round(rect.y * screen_h / map_h) + offset[1]
        x2 = round((rect.x + rect.width) * screen_w / map_w) + offset[0]
        y2 = round((rect.y + rect.height) * screen_h / map_h) + offset[1]

        return pygame.Rect(x1, y1, max(1, x2 - x1), max(1, y2 - y1))

    def draw_simplified_full_map(
        self,
        floors: List[pygame.Rect],
        walls: List[pygame.Rect],
        player,
        exit_door,
        entrance_door,
        level,
        camera: Camera,
        draw_player_marker: bool = True,
        offset: tuple[int, int] = (0, 0),
        clear_screen: bool = True,
        level_idx: int = None,
        obstacles: List[pygame.Rect] = None
    ):
        """
        Renderiza o mapa simplificado ajustado à janela usando apenas as paletas de cores,
        exibindo somente os tiles que já foram renderizados pela câmera (ativado ao segurar TAB).
        """
        screen_w = self.surface.get_width()
        screen_h = self.surface.get_height()

        target_level_idx = self.current_level_key if level_idx is None else level_idx
        explored = self.explored_tiles_by_level.setdefault(target_level_idx, set())

        if level_idx is None or level_idx == self.current_level_key:
            # Garante que a área atual da câmera também conste como renderizada
            viewport = camera.get_viewport_rect()
            v_start_x = max(0, (viewport.left // TILE_SIZE) * TILE_SIZE)
            v_end_x = min(camera.map_width, ((viewport.right // TILE_SIZE) + 1) * TILE_SIZE)
            v_start_y = max(0, (viewport.top // TILE_SIZE) * TILE_SIZE)
            v_end_y = min(camera.map_height, ((viewport.bottom // TILE_SIZE) + 1) * TILE_SIZE)

            for ty in range(v_start_y, v_end_y, TILE_SIZE):
                for tx in range(v_start_x, v_end_x, TILE_SIZE):
                    explored.add((tx, ty))

        # Área não explorada fica preta
        if clear_screen:
            self.surface.fill((0, 0, 0))

        tile_types = {}
        for rect in floors:
            tile_types[(rect.x, rect.y)] = "floor"
        for rect in walls:
            tile_types[(rect.x, rect.y)] = "wall"

        palette = MAP_PALETTES.get(self.player_theme_map, MAP_PALETTES[0])

        for tile_x, tile_y in explored:
            t_type = tile_types.get((tile_x, tile_y), "background")
            world_rect = pygame.Rect(tile_x, tile_y, TILE_SIZE, TILE_SIZE)
            pygame.draw.rect(
                self.surface,
                palette[t_type],
                self._scale_world_rect_to_screen(world_rect, camera, offset)
            )

        # Portas (mantém a cor da parede e desenha um X com a cor do chão)
        wall_color = palette["wall"]
        floor_color = palette["floor"]
        for door in (entrance_door, exit_door):
            if door is None:
                continue
            dx, dy = door["tile"]
            if (dx, dy) not in explored:
                continue
            door_world_rect = pygame.Rect(dx, dy, TILE_SIZE, TILE_SIZE)
            door_screen_rect = self._scale_world_rect_to_screen(
                door_world_rect, camera, offset
            )
            margin = max(2, door_screen_rect.width // 5)
            x1, y1 = door_screen_rect.left + margin, door_screen_rect.top + margin
            x2, y2 = door_screen_rect.right - margin, door_screen_rect.bottom - margin
            line_w = max(2, door_screen_rect.width // 6)
            pygame.draw.line(self.surface, floor_color, (x1, y1), (x2, y2), line_w)
            pygame.draw.line(self.surface, floor_color, (x1, y2), (x2, y1), line_w)

        # Obstáculos (círculo com a cor da parede nos tiles explorados)
        for obs_rect in (obstacles or []):
            obs_tile = (
                (obs_rect.x // TILE_SIZE) * TILE_SIZE,
                (obs_rect.y // TILE_SIZE) * TILE_SIZE,
            )
            if obs_tile not in explored:
                continue
            obs_screen_rect = self._scale_world_rect_to_screen(
                obs_rect, camera, offset
            )
            obs_radius = max(3, min(obs_screen_rect.width, obs_screen_rect.height) // 2)
            pygame.draw.circle(
                self.surface, wall_color, obs_screen_rect.center, obs_radius, width=2
            )

        # Jogador (círculo vermelho na posição correspondente no mapa, apenas no nível atual)
        if draw_player_marker:
            px = int(player.x * screen_w / camera.map_width) + offset[0]
            py = int(player.y * screen_h / camera.map_height) + offset[1]
            scale_factor = min(screen_w / camera.map_width, screen_h / camera.map_height)
            p_radius = max(5, int((TILE_SIZE * 0.35) * scale_factor))
            pygame.draw.circle(self.surface, COLOR_PLAYER, (px, py), p_radius)

    def render_map_slide_transition(
        self,
        from_data: dict,
        to_data: dict,
        direction: str,
        progress: float,
        player,
        hud_level_idx: int,
    ):
        """
        Desenha a transição deslizante entre dois mapas no TAB com um corredor
        ligando as portas de origem e destino.
        """
        screen_w = self.surface.get_width()
        screen_h = self.surface.get_height()

        dir_vectors = {
            "top": (0, -screen_h),
            "bottom": (0, screen_h),
            "left": (-screen_w, 0),
            "right": (screen_w, 0),
        }
        vx, vy = dir_vectors.get(direction, (0, 0))

        from_door = (
            from_data["exit_door"]
            if from_data["idx"] < to_data["idx"]
            else from_data["entrance_door"]
        )
        to_door = (
            to_data["entrance_door"]
            if from_data["idx"] < to_data["idx"]
            else to_data["exit_door"]
        )

        # Calcula o deslocamento perpendicular para alinhar a porta de origem com a de destino
        perp_x, perp_y = 0, 0
        if from_door is not None and to_door is not None:
            fx, fy = from_door["tile"]
            tx, ty = to_door["tile"]
            base_r1 = self._scale_world_rect_to_screen(
                pygame.Rect(fx, fy, TILE_SIZE, TILE_SIZE),
                from_data["camera"],
                (0, 0),
            )
            base_r2 = self._scale_world_rect_to_screen(
                pygame.Rect(tx, ty, TILE_SIZE, TILE_SIZE),
                to_data["camera"],
                (0, 0),
            )
            if direction in ("left", "right"):
                perp_y = base_r1.centery - base_r2.centery
            else:
                perp_x = base_r1.centerx - base_r2.centerx

        p = max(0.0, min(1.0, progress))
        split = 0.65
        if p <= split:
            t1 = p / split
            eased1 = 1.0 - (1.0 - t1) ** 3
            from_offset = (int(-vx * eased1), int(-vy * eased1))
            to_offset = (
                int(vx * (1.0 - eased1) + perp_x),
                int(vy * (1.0 - eased1) + perp_y),
            )
        else:
            t2 = (p - split) / (1.0 - split)
            eased2 = 1.0 - (1.0 - t2) ** 3
            from_offset = (
                int(-vx - perp_x * eased2),
                int(-vy - perp_y * eased2),
            )
            to_offset = (
                int(perp_x * (1.0 - eased2)),
                int(perp_y * (1.0 - eased2)),
            )

        self.surface.fill((0, 0, 0))

        # Desenha o corredor conectando a porta de saída/entrada entre os dois mapas
        if from_door is not None and to_door is not None:
            fx, fy = from_door["tile"]
            tx, ty = to_door["tile"]
            r1 = self._scale_world_rect_to_screen(
                pygame.Rect(fx, fy, TILE_SIZE, TILE_SIZE),
                from_data["camera"],
                from_offset,
            )
            r2 = self._scale_world_rect_to_screen(
                pygame.Rect(tx, ty, TILE_SIZE, TILE_SIZE),
                to_data["camera"],
                to_offset,
            )
            palette = MAP_PALETTES.get(self.player_theme_map, MAP_PALETTES[0])
            corridor_w = max(8, r1.width)
            pygame.draw.line(
                self.surface,
                palette["wall"],
                r1.center,
                r2.center,
                width=corridor_w + 6,
            )
            pygame.draw.line(
                self.surface,
                palette["floor"],
                r1.center,
                r2.center,
                width=corridor_w,
            )

        self.draw_simplified_full_map(
            from_data["floors"],
            from_data["walls"],
            player,
            from_data["exit_door"],
            from_data["entrance_door"],
            from_data["level"],
            from_data["camera"],
            draw_player_marker=from_data["draw_player_marker"],
            offset=from_offset,
            clear_screen=False,
            level_idx=from_data["idx"],
            obstacles=from_data.get("obstacles", []),
        )
        self.draw_simplified_full_map(
            to_data["floors"],
            to_data["walls"],
            player,
            to_data["exit_door"],
            to_data["entrance_door"],
            to_data["level"],
            to_data["camera"],
            draw_player_marker=to_data["draw_player_marker"],
            offset=to_offset,
            clear_screen=False,
            level_idx=to_data["idx"],
            obstacles=to_data.get("obstacles", []),
        )

        pygame.display.update()
