import pygame
from typing import List

class CollisionManager:
    @staticmethod
    def check_wall_collision(target_rect: pygame.Rect, walls: List[pygame.Rect]) -> bool:
        """
        Retorna True se target_rect colidir com qualquer uma das paredes.
        """
        for wall in walls:
            if wall.colliderect(target_rect):
                return True
        return False

    @staticmethod
    def check_trigger_collision(rect_a: pygame.Rect, rect_b: pygame.Rect) -> bool:
        """
        Retorna True se rect_a colidir com rect_b (por exemplo, player com saída).
        """
        return rect_a.colliderect(rect_b)
