import pygame
from config import WIDTH, HEIGHT, MAP_WIDTH, MAP_HEIGHT, TILE_SIZE


class Camera:
    def __init__(
        self,
        viewport_width: int = WIDTH,
        viewport_height: int = HEIGHT,
        map_width: int = MAP_WIDTH * TILE_SIZE,
        map_height: int = MAP_HEIGHT * TILE_SIZE,
    ):
        self.viewport_width = viewport_width
        self.viewport_height = viewport_height
        self.map_width = map_width
        self.map_height = map_height
        self.x = 0.0
        self.y = 0.0

    def set_map_size(self, map_width: int, map_height: int):
        """Atualiza os limites do mapa em pixels."""
        self.map_width = map_width
        self.map_height = map_height

    def update(self, target_x: float, target_y: float):
        """Centraliza a câmera no jogador, respeitando os limites do mapa."""
        desired_x = target_x - self.viewport_width / 2
        desired_y = target_y - self.viewport_height / 2

        max_x = max(0, self.map_width - self.viewport_width)
        max_y = max(0, self.map_height - self.viewport_height)

        self.x = max(0.0, min(float(max_x), desired_x))
        self.y = max(0.0, min(float(max_y), desired_y))

    def get_viewport_rect(self) -> pygame.Rect:
        """Retorna o retângulo da janela visível em coordenadas do mundo."""
        return pygame.Rect(
            int(self.x),
            int(self.y),
            self.viewport_width,
            self.viewport_height,
        )

    def is_visible(self, rect: pygame.Rect) -> bool:
        """Retorna True se o retângulo estiver dentro da área visível da câmera."""
        return self.get_viewport_rect().colliderect(rect)

    def apply(self, rect: pygame.Rect) -> pygame.Rect:
        """Converte um retângulo do mundo para coordenadas da tela."""
        return rect.move(-int(self.x), -int(self.y))

    def apply_point(self, x: float, y: float) -> tuple[int, int]:
        """Converte uma coordenada (x, y) do mundo para coordenadas da tela."""
        return int(x - self.x), int(y - self.y)

