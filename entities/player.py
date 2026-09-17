import pygame

class Player:
    def __init__(self, x: float = 0.0, y: float = 0.0, radius: float = 7.5, speed: float = 2.0):
        self.x = x
        self.y = y
        self.radius = radius
        self.speed = speed

    def set_position(self, x: float, y: float):
        self.x = x
        self.y = y

    def get_rect(self, x: float = None, y: float = None) -> pygame.Rect:
        px = self.x if x is None else x
        py = self.y if y is None else y
        size = self.radius * 2
        return pygame.Rect(px - self.radius, py - self.radius, size, size)

    def calculate_desired_position(self, keys) -> tuple[float, float]:
        new_x = self.x
        new_y = self.y

        if keys[pygame.K_w]:
            new_y -= self.speed
        elif keys[pygame.K_s]:
            new_y += self.speed
        elif keys[pygame.K_a]:
            new_x -= self.speed
        elif keys[pygame.K_d]:
            new_x += self.speed

        return new_x, new_y
