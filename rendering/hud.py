import pygame

class HUD:
    def __init__(self, surface: pygame.Surface):
        self.surface = surface
        pygame.font.init()
        self.font = pygame.font.SysFont("consolas", 24, bold=True)

        self.margin = 16
        self.padding_x = 14
        self.padding_y = 8
        self.bg_color = (15, 15, 20, 190)
        self.border_color = (220, 220, 230)
        self.text_color = (255, 255, 255)

    def draw(self, current_level_idx: int, level: dict = None, player=None):
        """
        Desenha a interface (HUD) sobre a tela.
        Preparado para receber futuramente barra de vida, habilidades, etc.
        """
        self._draw_level_indicator(current_level_idx)

    def _draw_level_indicator(self, current_level_idx: int):
        """Exibe a fase atual no canto superior direito."""
        stage_number = current_level_idx + 1
        label = f"Fase {stage_number}"

        text_surface = self.font.render(label, True, self.text_color)
        text_rect = text_surface.get_rect()

        box_width = text_rect.width + self.padding_x * 2
        box_height = text_rect.height + self.padding_y * 2

        #screen_width = self.surface.get_width()
        #box_x = screen_width - box_width - self.margin
        box_x = self.margin
        box_y = self.margin

        # Painel semitransparente para garantir leitura em qualquer bioma
        panel_surface = pygame.Surface((box_width, box_height), pygame.SRCALPHA)
        pygame.draw.rect(
            panel_surface,
            self.bg_color,
            panel_surface.get_rect(),
            border_radius=8,
        )
        pygame.draw.rect(
            panel_surface,
            self.border_color,
            panel_surface.get_rect(),
            width=2,
            border_radius=8,
        )

        self.surface.blit(panel_surface, (box_x, box_y))
        self.surface.blit(
            text_surface,
            (box_x + self.padding_x, box_y + self.padding_y),
        )

