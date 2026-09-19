import pygame
from typing import List, Tuple
from config import COLOR_BACKGROUND, COLOR_FLOOR, COLOR_WALL, COLOR_EXIT, COLOR_PLAYER, COLOR_ENTRANCE

class GameRenderer:
    def __init__(self, surface: pygame.Surface):
        self.surface = surface

    def clear(self):
        self.surface.fill(COLOR_BACKGROUND)

    def draw_map(self, floors: List[pygame.Rect], walls: List[pygame.Rect]):
        for rect in floors:
            pygame.draw.rect(self.surface, COLOR_FLOOR, rect)

        for rect in walls:
            pygame.draw.rect(self.surface, COLOR_WALL, rect)

    def draw_exit(self, exit_pos: Tuple[float, float], radius: float = 7.5):
        pygame.draw.circle(self.surface, COLOR_EXIT, (int(exit_pos[0]), int(exit_pos[1])), int(radius))

    def draw_entrance(self, entrance_pos: Tuple[float, float], radius: float = 7.5):
        pygame.draw.circle(self.surface, COLOR_ENTRANCE, (int(entrance_pos[0]), int(entrance_pos[1])), int(radius))

    def draw_player(self, player):
        pygame.draw.circle(self.surface, COLOR_PLAYER, (int(player.x), int(player.y)), int(player.radius))

    def render_frame(self, floors: List[pygame.Rect], walls: List[pygame.Rect], player, exit_pos: Tuple[float, float], entrance_pos: Tuple[float, float], current_level_idx: int):
        self.clear()
        self.draw_map(floors, walls)
        self.draw_exit(exit_pos, radius=player.radius)
        if current_level_idx > 0:
            self.draw_entrance(entrance_pos, radius=player.radius)
        self.draw_player(player)
        pygame.display.update()
