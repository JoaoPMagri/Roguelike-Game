import pygame
from config import (
    PLAYER_RADIUS,
    PLAYER_SPEED,
    PLAYER_HITBOX_WIDTH,
    PLAYER_HITBOX_HEIGHT,
    PLAYER_ANIMATION_COOLDOWN,
)


class Player:
    FRAMES_COUNT = 4

    def __init__(
        self,
        x: float = 0.0,
        y: float = 0.0,
        radius: float = PLAYER_RADIUS,
        speed: float = PLAYER_SPEED,
        hitbox_width: int = PLAYER_HITBOX_WIDTH,
        hitbox_height: int = PLAYER_HITBOX_HEIGHT,
    ):
        self.x = x
        self.y = y
        self.radius = radius
        self.speed = speed
        self.hitbox_width = hitbox_width
        self.hitbox_height = hitbox_height

        # Estado de direção e animação
        self.direction = "down"
        self.is_moving = False
        self.frame_index = 0
        self.last_frame_update = 0
        self.animation_cooldown = PLAYER_ANIMATION_COOLDOWN

    def set_position(self, x: float, y: float):
        self.x = x
        self.y = y

    def get_rect(self, x: float = None, y: float = None) -> pygame.Rect:
        px = self.x if x is None else x
        py = self.y if y is None else y
        return pygame.Rect(
            int(px - self.hitbox_width / 2),
            int(py - self.hitbox_height / 2),
            self.hitbox_width,
            self.hitbox_height,
        )

    def update_animation(self, moving: bool):
        if moving:
            current_time = pygame.time.get_ticks()
            if not self.is_moving:
                self.frame_index = 1
                self.last_frame_update = current_time
            elif current_time - self.last_frame_update >= self.animation_cooldown:
                self.frame_index = (self.frame_index + 1) % self.FRAMES_COUNT
                self.last_frame_update = current_time
        else:
            self.frame_index = 0

        self.is_moving = moving

    def calculate_desired_position(self, keys) -> tuple[float, float]:
        new_x = self.x
        new_y = self.y
        moving = False

        if keys[pygame.K_w]:
            new_y -= self.speed
            self.direction = "up"
            moving = True
        elif keys[pygame.K_s]:
            new_y += self.speed
            self.direction = "down"
            moving = True
        elif keys[pygame.K_a]:
            new_x -= self.speed
            self.direction = "left"
            moving = True
        elif keys[pygame.K_d]:
            new_x += self.speed
            self.direction = "right"
            moving = True

        self.update_animation(moving)
        return new_x, new_y
