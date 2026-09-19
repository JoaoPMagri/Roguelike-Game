from config import TILE_SIZE
from entities import player
import pygame
from typing import List, Tuple
import random
from config import MAP_PALETTES, COLOR_EXIT, COLOR_PLAYER, COLOR_ENTRANCE

class GameRenderer:
    def __init__(self, surface: pygame.Surface, map_type: int = 0):
        self.surface = surface
        self.palette = MAP_PALETTES[map_type]

        # =========================================================
        # CONTROLE DA TRANSIÇÃO
        # =========================================================

        # Guarda a decisão de cada tile:
        # {(x, y): True/False}
        self.transition_mask = {}

        # Momento em que a máscara foi atualizada
        self.transition_last_update = 0

        # Identifica qual transição está sendo exibida
        self.transition_key = None

        # Tempo entre cada novo sorteio da máscara (ms)
        self.transition_cooldown = 1000

    def draw_map(
        self,
        floors,
        walls,
        algorithm_a,
        algorithm_b=None,
        layout=None,
        reverse=False
    ):
        palette_a = MAP_PALETTES[algorithm_a]

        # ---------------------------------------------------------
        # Mapa puro
        # ---------------------------------------------------------
        if algorithm_b is None:
            self.surface.fill(palette_a["background"])

            for rect in floors:
                pygame.draw.rect(
                    self.surface,
                    palette_a["floor"],
                    rect
                )

            for rect in walls:
                pygame.draw.rect(
                    self.surface,
                    palette_a["wall"],
                    rect
                )

            return

        # ---------------------------------------------------------
        # Mapa intermediário
        # ---------------------------------------------------------
        palette_b = MAP_PALETTES[algorithm_b]

        # Background de cada submapa
        if layout == "horizontal":
            width = self.surface.get_width()
            half_width = width // 2

            if not reverse:
                pygame.draw.rect(
                    self.surface,
                    palette_a["background"],
                    pygame.Rect(0, 0, half_width, self.surface.get_height())
                )

                pygame.draw.rect(
                    self.surface,
                    palette_b["background"],
                    pygame.Rect(
                        half_width,
                        0,
                        width - half_width,
                        self.surface.get_height()
                    )
                )

            else:
                pygame.draw.rect(
                    self.surface,
                    palette_b["background"],
                    pygame.Rect(0, 0, half_width, self.surface.get_height())
                )

                pygame.draw.rect(
                    self.surface,
                    palette_a["background"],
                    pygame.Rect(
                        half_width,
                        0,
                        width - half_width,
                        self.surface.get_height()
                    )
                )

        elif layout == "vertical":
            height = self.surface.get_height()
            half_height = height // 2

            if not reverse:
                pygame.draw.rect(
                    self.surface,
                    palette_a["background"],
                    pygame.Rect(0, 0, self.surface.get_width(), half_height)
                )

                pygame.draw.rect(
                    self.surface,
                    palette_b["background"],
                    pygame.Rect(
                        0,
                        half_height,
                        self.surface.get_width(),
                        height - half_height
                    )
                )

            else:
                pygame.draw.rect(
                    self.surface,
                    palette_b["background"],
                    pygame.Rect(0, 0, self.surface.get_width(), half_height)
                )

                pygame.draw.rect(
                    self.surface,
                    palette_a["background"],
                    pygame.Rect(
                        0,
                        half_height,
                        self.surface.get_width(),
                        height - half_height
                    )
                )

        # ---------------------------------------------------------
        # Tiles
        # ---------------------------------------------------------
        for rect in floors:
            algorithm = self._get_algorithm_for_rect(
                rect,
                algorithm_a,
                algorithm_b,
                layout,
                reverse
            )

            pygame.draw.rect(
                self.surface,
                MAP_PALETTES[algorithm]["floor"],
                rect
            )

        for rect in walls:
            algorithm = self._get_algorithm_for_rect(
                rect,
                algorithm_a,
                algorithm_b,
                layout,
                reverse
            )

            pygame.draw.rect(
                self.surface,
                MAP_PALETTES[algorithm]["wall"],
                rect
            )

    def _get_algorithm_for_rect(
        self,
        rect,
        algorithm_a,
        algorithm_b,
        layout,
        reverse
    ):
        """
        Decide qual algoritmo gerou um determinado retângulo de tile.
        """
        if algorithm_b is None:
            return algorithm_a

        # Centro do retângulo em coordenadas de tile
        cx = rect.x + rect.width / 2
        cy = rect.y + rect.height / 2

        if layout == "horizontal":
            half_width = self.surface.get_width() // 2

            if not reverse:
                # A | B
                if cx < half_width:
                    return algorithm_a
                else:
                    return algorithm_b
            else:
                # B | A
                if cx < half_width:
                    return algorithm_b
                else:
                    return algorithm_a

        elif layout == "vertical":
            half_height = self.surface.get_height() // 2

            if not reverse:
                # A /
                # B
                if cy < half_height:
                    return algorithm_a
                else:
                    return algorithm_b
            else:
                # B /
                # A
                if cy < half_height:
                    return algorithm_b
                else:
                    return algorithm_a

        # Não deve acontecer
        return algorithm_a

    def draw_exit(self, exit_pos: Tuple[float, float], radius: float = 7.5):
        pygame.draw.circle(self.surface, COLOR_EXIT, (int(exit_pos[0]), int(exit_pos[1])), int(radius))

    def draw_entrance(self, entrance_pos: Tuple[float, float], radius: float = 7.5):
        pygame.draw.circle(self.surface, COLOR_ENTRANCE, (int(entrance_pos[0]), int(entrance_pos[1])), int(radius))

    def draw_player(self, player):
        pygame.draw.circle(self.surface, COLOR_PLAYER, (int(player.x), int(player.y)), int(player.radius))

    def render_frame(
        self,
        floors: List[pygame.Rect],
        walls: List[pygame.Rect],
        player,
        exit_pos: Tuple[float, float],
        entrance_pos: Tuple[float, float],
        current_level_idx: int,
        level
    ):
        # =========================================================
        # MAPA
        # =========================================================

        if level["type"] == "pure":
            # Mapa gerado por apenas um algoritmo
            self.draw_map(
                floors,
                walls,
                algorithm_a=level["algorithm"]
            )

        else:
            # Mapa intermediário: algoritmo A + algoritmo B
            self.draw_map(
                floors,
                walls,
                algorithm_a=level["algorithm_a"],
                algorithm_b=level["algorithm_b"],
                layout=level["layout"],
                reverse=level["reverse"]
            )

            self.draw_transition(
                floors,
                walls,
                algorithm_a=level["algorithm_a"],
                algorithm_b=level["algorithm_b"],
                layout=level["layout"],
                reverse=level["reverse"]
            )

        # =========================================================
        # EXIT
        # =========================================================

        self.draw_exit(
            exit_pos,
            radius=player.radius
        )

        # =========================================================
        # ENTRANCE
        # =========================================================

        if current_level_idx > 0:
            self.draw_entrance(
                entrance_pos,
                radius=player.radius
            )

        # =========================================================
        # PLAYER
        # =========================================================

        self.draw_player(player)

        pygame.display.update()

    
    def _get_algorithm_for_rect(
        self,
        rect,
        algorithm_a,
        algorithm_b,
        layout,
        reverse
    ):
        if layout == "horizontal":
            boundary = self.surface.get_width() // 2

            first_algorithm = algorithm_b if reverse else algorithm_a
            second_algorithm = algorithm_a if reverse else algorithm_b

            if rect.centerx < boundary:
                return first_algorithm

            return second_algorithm

        if layout == "vertical":
            boundary = self.surface.get_height() // 2

            first_algorithm = algorithm_b if reverse else algorithm_a
            second_algorithm = algorithm_a if reverse else algorithm_b

            if rect.centery < boundary:
                return first_algorithm

            return second_algorithm

        return algorithm_a

    def draw_transition(
        self,
        floors,
        walls,
        algorithm_a,
        algorithm_b,
        layout,
        reverse=False
    ):
        """
        Cria uma transição dinâmica entre dois mapas.

        Cada tile da região de transição recebe uma decisão:

            algoritmo A
            ou
            algoritmo B

        A probabilidade de utilizar o segundo mapa aumenta
        conforme o progress avança.

        A máscara permanece congelada durante o cooldown.
        """

        # =========================================================
        # IDENTIFICAÇÃO DA TRANSIÇÃO
        # =========================================================

        transition_key = (
            algorithm_a,
            algorithm_b,
            layout,
            reverse
        )

        # Se mudou de mapa/transição,
        # cria uma nova máscara
        if transition_key != self.transition_key:

            self.transition_key = transition_key
            self.transition_mask.clear()

            # Força geração imediata
            self.transition_last_update = 0

        # =========================================================
        # COOLDOWN
        # =========================================================

        current_time = pygame.time.get_ticks()

        if (
            current_time - self.transition_last_update
            >= self.transition_cooldown
        ):

            self.transition_mask.clear()

            self.transition_last_update = current_time

        # =========================================================
        # DEFINIR QUAL MAPA ESTÁ EM CADA LADO
        # =========================================================

        if reverse:

            first_algorithm = algorithm_b
            second_algorithm = algorithm_a

        else:

            first_algorithm = algorithm_a
            second_algorithm = algorithm_b

        first_palette = MAP_PALETTES[first_algorithm]
        second_palette = MAP_PALETTES[second_algorithm]

        # =========================================================
        # IDENTIFICAR TIPO DOS TILES
        # =========================================================

        tile_types = {}

        for rect in floors:
            tile_types[(rect.x, rect.y)] = "floor"

        for rect in walls:
            tile_types[(rect.x, rect.y)] = "wall"

        # =========================================================
        # DESENHAR UM TILE
        # =========================================================

        def draw_tile(x, y, algorithm):

            palette = MAP_PALETTES[algorithm]

            tile_type = tile_types.get((x, y))

            # Background
            if tile_type is None:
                color = palette["background"]

            # Floor
            elif tile_type == "floor":
                color = palette["floor"]

            # Wall
            else:
                color = palette["wall"]

            pygame.draw.rect(
                self.surface,
                color,
                pygame.Rect(
                    x,
                    y,
                    TILE_SIZE,
                    TILE_SIZE
                )
            )

        # =========================================================
        # TRANSIÇÃO HORIZONTAL
        # =========================================================

        if layout == "horizontal":

            width = self.surface.get_width()
            height = self.surface.get_height()

            start = width / 3
            end = (width * 2) / 3

            x = start

            while x < end:

                # -------------------------------------------------
                # 0 -> 1
                # -------------------------------------------------

                progress = (
                    (x - start)
                    / (end - start)
                )

                progress = max(
                    0.0,
                    min(1.0, progress)
                )

                # -------------------------------------------------
                # Curva da transição
                # -------------------------------------------------

                chance = progress ** 2

                y = 0

                while y < height:

                    tile_x = int(x // TILE_SIZE) * TILE_SIZE
                    tile_y = int(y // TILE_SIZE) * TILE_SIZE

                    tile_position = (tile_x, tile_y)

                    # -------------------------------------------------
                    # Primeiro acesso ao tile
                    # -------------------------------------------------

                    if tile_position not in self.transition_mask:

                        if random.random() < chance:

                            # Segundo mapa
                            self.transition_mask[tile_position] = (
                                second_algorithm
                            )

                        else:

                            # Primeiro mapa
                            self.transition_mask[tile_position] = (
                                first_algorithm
                            )

                    # -------------------------------------------------
                    # Desenha o algoritmo armazenado
                    # -------------------------------------------------

                    algorithm = self.transition_mask[tile_position]

                    draw_tile(
                        tile_x,
                        tile_y,
                        algorithm
                    )

                    y += TILE_SIZE

                x += TILE_SIZE

        # =========================================================
        # TRANSIÇÃO VERTICAL
        # =========================================================

        elif layout == "vertical":

            width = self.surface.get_width()
            height = self.surface.get_height()

            start = height / 3
            end = (height * 2) / 3

            y = start

            while y < end:

                # -------------------------------------------------
                # 0 -> 1
                # -------------------------------------------------

                progress = (
                    (y - start)
                    / (end - start)
                )

                progress = max(
                    0.0,
                    min(1.0, progress)
                )

                # -------------------------------------------------
                # Curva da transição
                # -------------------------------------------------

                chance = progress ** 2

                x = 0

                while x < width:

                    tile_x = int(x // TILE_SIZE) * TILE_SIZE
                    tile_y = int(y // TILE_SIZE) * TILE_SIZE

                    tile_position = (tile_x, tile_y)

                    # -------------------------------------------------
                    # Primeiro acesso ao tile
                    # -------------------------------------------------

                    if tile_position not in self.transition_mask:

                        if random.random() < chance:

                            # Segundo mapa
                            self.transition_mask[tile_position] = (
                                second_algorithm
                            )

                        else:

                            # Primeiro mapa
                            self.transition_mask[tile_position] = (
                                first_algorithm
                            )

                    # -------------------------------------------------
                    # Desenha o algoritmo armazenado
                    # -------------------------------------------------

                    algorithm = self.transition_mask[tile_position]

                    draw_tile(
                        tile_x,
                        tile_y,
                        algorithm
                    )

                    x += TILE_SIZE

                y += TILE_SIZE
