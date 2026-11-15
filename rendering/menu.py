import pygame
from config import (
    CHARACTER_OPTIONS,
    SPRITE_SIZE,
    RESOLUTION_OPTIONS,
    PROCESSING_SPEED_OPTIONS,
    VOLUME_OPTIONS,
    WIDTH,
    HEIGHT,
    FPS,
    VOLUME,
)
from persistence import get_resource_path


class SettingsMenu:
    """
    Submenu de configurações com valores pré-definidos para:
    - Tamanho da janela (RESOLUTION_OPTIONS)
    - Taxa de quadros / FPS (FPS_OPTIONS)
    Pode ser utilizado tanto no Menu Inicial quanto no Menu de Pause.
    """

    def __init__(
        self,
        surface: pygame.Surface,
        current_width: int = WIDTH,
        current_height: int = HEIGHT,
        current_fps: int = FPS,
        current_volume: float = VOLUME,
    ):
        self.surface = surface
        pygame.font.init()

        self.title_font = pygame.font.SysFont("consolas", 36, bold=True)
        self.label_font = pygame.font.SysFont("consolas", 22, bold=True)
        self.value_font = pygame.font.SysFont("consolas", 22, bold=True)
        self.hint_font = pygame.font.SysFont("consolas", 15)

        self.resolutions = RESOLUTION_OPTIONS
        self.speed_options = PROCESSING_SPEED_OPTIONS
        self.volume_options = VOLUME_OPTIONS

        self.res_idx = 0
        self.fps_idx = 0
        self.vol_idx = 0
        self.selected_row = 0  # 0 = Resolução, 1 = Velocidade, 2 = Volume, 3 = Aplicar, 4 = Voltar

        self.row_rects = []
        self.left_arrow_rects = {}
        self.right_arrow_rects = {}
        self.apply_btn_rect = pygame.Rect(0, 0, 230, 50)
        self.back_btn_rect = pygame.Rect(0, 0, 230, 50)

        self.sync_current_values(current_width, current_height, current_fps, current_volume)

    def sync_current_values(
        self, width: int, height: int, fps: int, volume: float = None
    ):
        if (width, height) in self.resolutions:
            self.res_idx = self.resolutions.index((width, height))
        else:
            self.res_idx = 0

        mult = fps / FPS
        self.fps_idx = min(
            range(len(self.speed_options)),
            key=lambda i: abs(self.speed_options[i] - mult),
        )
        if volume is not None:
            self.vol_idx = min(
                range(len(self.volume_options)),
                key=lambda i: abs(self.volume_options[i] - volume),
            )

        self.selected_row = 0

    def _update_layout(self):
        screen_w = self.surface.get_width()
        screen_h = self.surface.get_height()

        panel_w = min(620, screen_w - 60)
        row_h = 68
        start_y = screen_h // 2 - 110
        center_x = screen_w // 2

        res_rect = pygame.Rect(center_x - panel_w // 2, start_y, panel_w, row_h)
        fps_rect = pygame.Rect(center_x - panel_w // 2, start_y + 82, panel_w, row_h)
        vol_rect = pygame.Rect(center_x - panel_w // 2, start_y + 164, panel_w, row_h)

        btn_w = 220
        btn_h = 52
        btn_y = start_y + 256
        self.back_btn_rect = pygame.Rect(center_x - btn_w - 16, btn_y, btn_w, btn_h)
        self.apply_btn_rect = pygame.Rect(center_x + 16, btn_y, btn_w, btn_h)

        self.row_rects = [
            res_rect,
            fps_rect,
            vol_rect,
            self.apply_btn_rect,
            self.back_btn_rect,
        ]

        # Botões "<" e ">" dentro das linhas 0, 1 e 2
        arrow_size = 42
        for row_idx, r in enumerate((res_rect, fps_rect, vol_rect)):
            right_arrow = pygame.Rect(
                r.right - arrow_size - 16,
                r.centery - arrow_size // 2,
                arrow_size,
                arrow_size,
            )
            left_arrow = pygame.Rect(
                right_arrow.left - 210 - arrow_size,
                r.centery - arrow_size // 2,
                arrow_size,
                arrow_size,
            )
            self.left_arrow_rects[row_idx] = left_arrow
            self.right_arrow_rects[row_idx] = right_arrow

    def _change_value(self, row: int, step: int):
        if row == 0:
            self.res_idx = (self.res_idx + step) % len(self.resolutions)
        elif row == 1:
            self.fps_idx = (self.fps_idx + step) % len(self.speed_options)
        elif row == 2:
            self.vol_idx = (self.vol_idx + step) % len(self.volume_options)

    def _build_apply_result(self) -> dict:
        w, h = self.resolutions[self.res_idx]
        mult = self.speed_options[self.fps_idx]
        fps = max(1, int(round(FPS * mult)))
        vol = self.volume_options[self.vol_idx]
        return {
            "action": "apply_settings",
            "width": w,
            "height": h,
            "fps": fps,
            "volume": vol,
        }

    def handle_event(self, event: pygame.event.Event):
        self._update_layout()

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                return {"action": "back"}

            if event.key in (pygame.K_UP, pygame.K_w):
                self.selected_row = (self.selected_row - 1) % 5
            elif event.key in (pygame.K_DOWN, pygame.K_s):
                self.selected_row = (self.selected_row + 1) % 5
            elif event.key in (pygame.K_LEFT, pygame.K_a):
                if self.selected_row in (0, 1, 2):
                    self._change_value(self.selected_row, -1)
                elif self.selected_row == 3:
                    self.selected_row = 4
                elif self.selected_row == 4:
                    self.selected_row = 3
            elif event.key in (pygame.K_RIGHT, pygame.K_d):
                if self.selected_row in (0, 1, 2):
                    self._change_value(self.selected_row, 1)
                elif self.selected_row == 3:
                    self.selected_row = 4
                elif self.selected_row == 4:
                    self.selected_row = 3
            elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                if self.selected_row in (0, 1, 2):
                    self._change_value(self.selected_row, 1)
                elif self.selected_row == 3:
                    return self._build_apply_result()
                elif self.selected_row == 4:
                    return {"action": "back"}

        elif event.type == pygame.MOUSEMOTION:
            for idx, rect in enumerate(self.row_rects):
                if rect.collidepoint(event.pos):
                    self.selected_row = idx
                    break

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for row_idx in (0, 1, 2):
                if self.left_arrow_rects[row_idx].collidepoint(event.pos):
                    self.selected_row = row_idx
                    self._change_value(row_idx, -1)
                    return None
                if self.right_arrow_rects[row_idx].collidepoint(event.pos):
                    self.selected_row = row_idx
                    self._change_value(row_idx, 1)
                    return None

            if self.apply_btn_rect.collidepoint(event.pos):
                return self._build_apply_result()
            if self.back_btn_rect.collidepoint(event.pos):
                return {"action": "back"}

        return None

    def draw(self, overlay_mode: bool = False):
        self._update_layout()
        screen_w = self.surface.get_width()
        screen_h = self.surface.get_height()

        if not overlay_mode:
            self.surface.fill((14, 16, 24))

        # Caixa central quando em overlay (pause)
        panel_w = min(680, screen_w - 30)
        panel_h = 500
        panel_rect = pygame.Rect(
            (screen_w - panel_w) // 2,
            (screen_h - panel_h) // 2,
            panel_w,
            panel_h,
        )

        if overlay_mode:
            pygame.draw.rect(
                self.surface,
                (18, 21, 32),
                panel_rect,
                border_radius=16,
            )
            pygame.draw.rect(
                self.surface,
                (80, 90, 120),
                panel_rect,
                width=2,
                border_radius=16,
            )

        title_surf = self.title_font.render(
            "CONFIGURAÇÕES", True, (245, 245, 250)
        )
        title_rect = title_surf.get_rect(
            center=(screen_w // 2, panel_rect.top + 48)
        )
        self.surface.blit(title_surf, title_rect)

        w, h = self.resolutions[self.res_idx]
        mult = self.speed_options[self.fps_idx]
        speed_label = f"{mult:g}x".replace(".", ",")
        vol = self.volume_options[self.vol_idx]
        vol_label = f"{int(round(vol * 100))}%"

        rows_data = [
            ("Tamanho da Janela", f"{w} x {h}"),
            ("Velocidade de Processamento", speed_label),
            ("Volume", vol_label),
        ]

        for row_idx, (label_text, val_text) in enumerate(rows_data):
            rect = self.row_rects[row_idx]
            is_sel = self.selected_row == row_idx

            bg_color = (32, 38, 56) if is_sel else (24, 28, 40)
            border_color = (15, 227, 208) if is_sel else (65, 72, 95)

            pygame.draw.rect(self.surface, bg_color, rect, border_radius=10)
            pygame.draw.rect(
                self.surface,
                border_color,
                rect,
                width=3 if is_sel else 2,
                border_radius=10,
            )

            lbl_surf = self.label_font.render(
                label_text, True, (230, 235, 245)
            )
            lbl_rect = lbl_surf.get_rect(midleft=(rect.left + 22, rect.centery))
            self.surface.blit(lbl_surf, lbl_rect)

            left_btn = self.left_arrow_rects[row_idx]
            right_btn = self.right_arrow_rects[row_idx]

            for arrow_rect, symbol in ((left_btn, "<"), (right_btn, ">")):
                pygame.draw.rect(
                    self.surface,
                    (42, 50, 72),
                    arrow_rect,
                    border_radius=8,
                )
                pygame.draw.rect(
                    self.surface,
                    border_color,
                    arrow_rect,
                    width=2,
                    border_radius=8,
                )
                sym_surf = self.value_font.render(symbol, True, (245, 245, 250))
                self.surface.blit(
                    sym_surf, sym_surf.get_rect(center=arrow_rect.center)
                )

            val_center_x = (left_btn.right + right_btn.left) // 2
            val_surf = self.value_font.render(
                val_text, True, (15, 227, 208) if is_sel else (210, 215, 230)
            )
            self.surface.blit(
                val_surf, val_surf.get_rect(center=(val_center_x, rect.centery))
            )

        # Botão Voltar
        is_back_sel = self.selected_row == 4
        pygame.draw.rect(
            self.surface,
            (46, 52, 72) if is_back_sel else (32, 36, 50),
            self.back_btn_rect,
            border_radius=10,
        )
        pygame.draw.rect(
            self.surface,
            (240, 240, 245) if is_back_sel else (90, 98, 122),
            self.back_btn_rect,
            width=3 if is_back_sel else 2,
            border_radius=10,
        )
        back_surf = self.label_font.render("VOLTAR", True, (235, 238, 245))
        self.surface.blit(
            back_surf, back_surf.get_rect(center=self.back_btn_rect.center)
        )

        # Botão Aplicar
        is_apply_sel = self.selected_row == 3
        pygame.draw.rect(
            self.surface,
            (15, 227, 208) if is_apply_sel else (12, 165, 152),
            self.apply_btn_rect,
            border_radius=10,
        )
        if is_apply_sel:
            pygame.draw.rect(
                self.surface,
                (255, 255, 255),
                self.apply_btn_rect,
                width=3,
                border_radius=10,
            )
        apply_surf = self.label_font.render("APLICAR", True, (12, 14, 20))
        self.surface.blit(
            apply_surf, apply_surf.get_rect(center=self.apply_btn_rect.center)
        )

        if overlay_mode:
            hint_lines = [
                "[W/S] Linha  |  [A/D ou Setas] Alterar Valor",
                "[ENTER] Confirmar  |  [ESC] Voltar",
            ]
            for idx_line, line_text in enumerate(hint_lines):
                hint_surf = self.hint_font.render(line_text, True, (145, 152, 175))
                hint_y = panel_rect.bottom - 38 + idx_line * 20
                self.surface.blit(
                    hint_surf, hint_surf.get_rect(center=(screen_w // 2, hint_y))
                )
        else:
            hint_surf = self.hint_font.render(
                "[W/S] Linha   |   [A/D ou Setas] Alterar Valor   |   [ENTER] Confirmar   |   [ESC] Voltar",
                True,
                (145, 152, 175),
            )
            self.surface.blit(
                hint_surf, hint_surf.get_rect(center=(screen_w // 2, screen_h - 32))
            )


class PauseMenu:
    """
    Menu de Pause exibido sobre o jogo ao pressionar ESC durante a partida.
    Opções:
    - Continuar
    - Configurações
    - Voltar ao Menu Inicial
    """

    def __init__(self, surface: pygame.Surface, settings_menu: SettingsMenu):
        self.surface = surface
        self.settings_menu = settings_menu
        pygame.font.init()

        self.title_font = pygame.font.SysFont("consolas", 40, bold=True)
        self.option_font = pygame.font.SysFont("consolas", 22, bold=True)
        self.hint_font = pygame.font.SysFont("consolas", 15)

        self.mode = "main"  # "main" ou "settings"
        self.selected_idx = 0
        self.options = [
            {"id": "resume", "label": "CONTINUAR"},
            {"id": "settings", "label": "CONFIGURAÇÕES"},
            {"id": "main_menu", "label": "VOLTAR AO MENU INICIAL"},
        ]
        self.button_rects = []

    def reset(self):
        self.mode = "main"
        self.selected_idx = 0

    def _update_layout(self):
        screen_w = self.surface.get_width()
        screen_h = self.surface.get_height()

        btn_w = 380
        btn_h = 58
        gap = 18
        total_h = len(self.options) * btn_h + (len(self.options) - 1) * gap
        start_y = (screen_h - total_h) // 2 + 20
        btn_x = (screen_w - btn_w) // 2

        self.button_rects = [
            pygame.Rect(btn_x, start_y + i * (btn_h + gap), btn_w, btn_h)
            for i in range(len(self.options))
        ]

    def handle_event(
        self,
        event: pygame.event.Event,
        current_width: int,
        current_height: int,
        current_fps: int,
    ):
        if self.mode == "settings":
            res = self.settings_menu.handle_event(event)
            if res is not None:
                if res["action"] == "back":
                    self.mode = "main"
                    return None
                if res["action"] == "apply_settings":
                    self.mode = "main"
                    return res
            return None

        self._update_layout()

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                return {"action": "resume"}
            if event.key in (pygame.K_UP, pygame.K_w):
                self.selected_idx = (self.selected_idx - 1) % len(self.options)
            elif event.key in (pygame.K_DOWN, pygame.K_s):
                self.selected_idx = (self.selected_idx + 1) % len(self.options)
            elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                return self._trigger_option(
                    self.options[self.selected_idx]["id"],
                    current_width,
                    current_height,
                    current_fps,
                )

        elif event.type == pygame.MOUSEMOTION:
            for idx, rect in enumerate(self.button_rects):
                if rect.collidepoint(event.pos):
                    self.selected_idx = idx
                    break

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for idx, rect in enumerate(self.button_rects):
                if rect.collidepoint(event.pos):
                    self.selected_idx = idx
                    return self._trigger_option(
                        self.options[idx]["id"],
                        current_width,
                        current_height,
                        current_fps,
                    )

        return None

    def _trigger_option(
        self,
        opt_id: str,
        current_width: int,
        current_height: int,
        current_fps: int,
    ):
        if opt_id == "resume":
            return {"action": "resume"}
        if opt_id == "settings":
            self.settings_menu.sync_current_values(
                current_width, current_height, current_fps
            )
            self.mode = "settings"
            return None
        if opt_id == "main_menu":
            return {"action": "main_menu"}
        return None

    def draw(self):
        self._update_layout()
        screen_w = self.surface.get_width()
        screen_h = self.surface.get_height()

        # Película escura semitransparente sobre o jogo pausado
        overlay = pygame.Surface((screen_w, screen_h), pygame.SRCALPHA)
        overlay.fill((10, 12, 20, 185))
        self.surface.blit(overlay, (0, 0))

        if self.mode == "settings":
            self.settings_menu.draw(overlay_mode=True)
            pygame.display.update()
            return

        panel_w = 460
        panel_h = 360
        panel_rect = pygame.Rect(
            (screen_w - panel_w) // 2,
            (screen_h - panel_h) // 2,
            panel_w,
            panel_h,
        )

        pygame.draw.rect(
            self.surface,
            (18, 21, 32),
            panel_rect,
            border_radius=16,
        )
        pygame.draw.rect(
            self.surface,
            (80, 90, 120),
            panel_rect,
            width=2,
            border_radius=16,
        )

        title_surf = self.title_font.render("JOGO PAUSADO", True, (245, 245, 250))
        title_rect = title_surf.get_rect(
            center=(screen_w // 2, panel_rect.top + 52)
        )
        self.surface.blit(title_surf, title_rect)

        for idx, opt in enumerate(self.options):
            rect = self.button_rects[idx]
            is_sel = idx == self.selected_idx

            bg_color = (34, 42, 62) if is_sel else (24, 28, 40)
            border_color = (15, 227, 208) if is_sel else (70, 78, 102)
            text_color = (255, 255, 255) if is_sel else (210, 215, 228)

            pygame.draw.rect(self.surface, bg_color, rect, border_radius=10)
            pygame.draw.rect(
                self.surface,
                border_color,
                rect,
                width=3 if is_sel else 2,
                border_radius=10,
            )

            lbl_surf = self.option_font.render(opt["label"], True, text_color)
            self.surface.blit(lbl_surf, lbl_surf.get_rect(center=rect.center))

        hint_lines = [
            "[W/S] Navegar  |  [ENTER] Confirmar",
            "[ESC] Continuar",
        ]
        for idx_line, line_text in enumerate(hint_lines):
            hint_surf = self.hint_font.render(line_text, True, (145, 152, 175))
            y_pos = panel_rect.bottom - 32 + idx_line * 18
            self.surface.blit(
                hint_surf,
                hint_surf.get_rect(center=(screen_w // 2, y_pos)),
            )

        pygame.display.update()


class StartMenu:
    """
    Menu inicial:
    1. Tela principal ("main"): Jogar, Configurações, Sair.
    2. Seleção de save ("save_select"): 4 cards de slots (carregar, novo jogo ou excluir).
    3. Seleção de personagem ("character_select"): escolha entre os 4 personagens.
    4. Configurações ("settings"): ajuste de janela e FPS.
    """

    PREVIEW_SIZE = 128
    FRAMES_COUNT = 4
    ANIMATION_COOLDOWN = 160

    def __init__(
        self,
        surface: pygame.Surface,
        settings_menu: SettingsMenu,
        saves: list = None,
    ):
        self.surface = surface
        self.settings_menu = settings_menu
        pygame.font.init()

        self.title_font = pygame.font.SysFont("consolas", 46, bold=True)
        self.subtitle_font = pygame.font.SysFont("consolas", 24, bold=True)
        self.card_font = pygame.font.SysFont("consolas", 20, bold=True)
        self.hint_font = pygame.font.SysFont("consolas", 18)

        self.characters = CHARACTER_OPTIONS
        self.selected_idx = 0
        self.frame_index = 0
        self.last_anim_update = 0

        self.previews = self._load_character_previews()
        self.card_rects = []
        self.save_card_rects = []
        self.delete_button_rects = []
        self.save_back_button_rect = pygame.Rect(0, 0, 220, 48)
        self.start_button_rect = pygame.Rect(0, 0, 260, 54)
        self.back_button_rect = pygame.Rect(0, 0, 160, 44)
        self.detail_start_rect = pygame.Rect(0, 0, 240, 50)
        self.detail_back_rect = pygame.Rect(0, 0, 200, 50)
        self.detail_selected_btn = 0

        self.screen_mode = "main"
        self.saves = saves if saves is not None else [None, None, None, None]
        self.selected_slot_idx = 0
        self.selected_save_slot = 1
        self.main_options = []
        self.main_button_rects = []
        self.main_selected_idx = 0
        self.refresh_saves(self.saves)

    def refresh_saves(self, saves: list, reset_to_main: bool = True):
        """Atualiza os 4 slots de save exibidos no menu."""
        self.saves = saves if saves is not None else [None, None, None, None]
        if reset_to_main:
            self.screen_mode = "main"

        occupied_count = sum(1 for s in self.saves if s is not None)
        play_subtitle = (
            f"{occupied_count}/4 slots ocupados"
            if occupied_count > 0
            else "Escolher um slot para iniciar"
        )

        self.main_options = [
            {
                "id": "play",
                "label": "JOGAR",
                "subtitle": play_subtitle,
                "enabled": True,
            },
            {
                "id": "settings",
                "label": "CONFIGURAÇÕES",
                "subtitle": "Ajustar tamanho da janela e FPS",
                "enabled": True,
            },
            {
                "id": "quit",
                "label": "SAIR",
                "subtitle": None,
                "enabled": True,
            },
        ]

        self.main_selected_idx = 0

    def _load_character_previews(self) -> list[list[pygame.Surface]]:
        """Carrega os 4 frames frontais (linha 0) de cada personagem para o menu."""
        previews = []

        for char in self.characters:
            full_path = get_resource_path(char["sprite_path"])
            sheet = pygame.image.load(full_path).convert_alpha()
            frames = []
            for col in range(self.FRAMES_COUNT):
                rect = pygame.Rect(col * SPRITE_SIZE, 0, SPRITE_SIZE, SPRITE_SIZE)
                raw = sheet.subsurface(rect)
                scaled = pygame.transform.scale(
                    raw, (self.PREVIEW_SIZE, self.PREVIEW_SIZE)
                )
                frames.append(scaled)
            previews.append(frames)

        return previews

    def _update_layout(self):
        screen_w = self.surface.get_width()
        screen_h = self.surface.get_height()

        # Layout da tela principal ("main")
        btn_w = 420
        btn_h = 66
        btn_gap = 16
        total_main_h = (
            len(self.main_options) * btn_h
            + (len(self.main_options) - 1) * btn_gap
        )
        start_y = (screen_h - total_main_h) // 2 + 30
        btn_x = (screen_w - btn_w) // 2

        self.main_button_rects = [
            pygame.Rect(btn_x, start_y + i * (btn_h + btn_gap), btn_w, btn_h)
            for i in range(len(self.main_options))
        ]

        # Layout da seleção de personagens ("character_select")
        card_w = min(240, (screen_w - 140) // 4)
        card_h = min(300, screen_h - 230)
        gap = min(32, max(12, (screen_w - 4 * card_w) // 5))
        count = len(self.characters)
        total_w = count * card_w + (count - 1) * gap
        start_x = (screen_w - total_w) // 2
        card_y = (screen_h - card_h) // 2 + 8

        self.card_rects = [
            pygame.Rect(start_x + i * (card_w + gap), card_y, card_w, card_h)
            for i in range(count)
        ]

        self.save_card_rects = list(self.card_rects)
        self.delete_button_rects = [
            pygame.Rect(r.x + 24, r.bottom - 42, r.width - 48, 30)
            for r in self.save_card_rects
        ]

        btn_y = min(screen_h - 75, card_y + card_h + 22)
        self.save_back_button_rect = pygame.Rect(
            screen_w // 2 - 110,
            btn_y,
            220,
            48,
        )
        self.start_button_rect = pygame.Rect(
            screen_w // 2 + 10,
            btn_y,
            220,
            48,
        )
        self.back_button_rect = pygame.Rect(
            screen_w // 2 - 230,
            btn_y,
            220,
            48,
        )

    def _move_main_selection(self, step: int):
        count = len(self.main_options)
        idx = self.main_selected_idx
        for _ in range(count):
            idx = (idx + step) % count
            if self.main_options[idx]["enabled"]:
                self.main_selected_idx = idx
                break

    def _trigger_main_option(
        self,
        option_id: str,
        current_width: int,
        current_height: int,
        current_fps: int,
    ):
        if option_id == "play":
            self.screen_mode = "save_select"
            return None
        if option_id == "settings":
            self.settings_menu.sync_current_values(
                current_width, current_height, current_fps
            )
            self.screen_mode = "settings"
            return None
        if option_id == "quit":
            return {"action": "quit"}
        return None

    def handle_event(
        self,
        event: pygame.event.Event,
        current_width: int = WIDTH,
        current_height: int = HEIGHT,
        current_fps: int = FPS,
    ):
        self._update_layout()

        if self.screen_mode == "settings":
            res = self.settings_menu.handle_event(event)
            if res is not None:
                if res["action"] == "back":
                    self.screen_mode = "main"
                    return None
                if res["action"] == "apply_settings":
                    self.screen_mode = "main"
                    return res
            return None

        if self.screen_mode == "main":
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_UP, pygame.K_w):
                    self._move_main_selection(-1)
                elif event.key in (pygame.K_DOWN, pygame.K_s):
                    self._move_main_selection(1)
                elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                    opt = self.main_options[self.main_selected_idx]
                    if opt["enabled"]:
                        return self._trigger_main_option(
                            opt["id"],
                            current_width,
                            current_height,
                            current_fps,
                        )

            elif event.type == pygame.MOUSEMOTION:
                for idx, rect in enumerate(self.main_button_rects):
                    if rect.collidepoint(event.pos) and self.main_options[idx]["enabled"]:
                        self.main_selected_idx = idx
                        break

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for idx, rect in enumerate(self.main_button_rects):
                    if rect.collidepoint(event.pos) and self.main_options[idx]["enabled"]:
                        self.main_selected_idx = idx
                        return self._trigger_main_option(
                            self.main_options[idx]["id"],
                            current_width,
                            current_height,
                            current_fps,
                        )

            return None

        if self.screen_mode == "character_detail":
            return self._handle_character_detail_event(event)

        if self.screen_mode == "save_select":
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.screen_mode = "main"
                    return None
                if event.key in (pygame.K_LEFT, pygame.K_a):
                    self.selected_slot_idx = (self.selected_slot_idx - 1) % 4
                elif event.key in (pygame.K_RIGHT, pygame.K_d):
                    self.selected_slot_idx = (self.selected_slot_idx + 1) % 4
                elif event.key in (pygame.K_DELETE, pygame.K_BACKSPACE):
                    if self.saves[self.selected_slot_idx] is not None:
                        return {
                            "action": "delete_slot",
                            "slot": self.selected_slot_idx + 1,
                        }
                elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                    slot_num = self.selected_slot_idx + 1
                    if self.saves[self.selected_slot_idx] is not None:
                        return {"action": "load_slot", "slot": slot_num}
                    self.selected_save_slot = slot_num
                    self.screen_mode = "character_select"
                    return None

            elif event.type == pygame.MOUSEMOTION:
                for idx, rect in enumerate(self.save_card_rects):
                    if rect.collidepoint(event.pos):
                        self.selected_slot_idx = idx
                        break

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for idx, del_rect in enumerate(self.delete_button_rects):
                    if self.saves[idx] is not None and del_rect.collidepoint(event.pos):
                        self.selected_slot_idx = idx
                        return {"action": "delete_slot", "slot": idx + 1}

                for idx, rect in enumerate(self.save_card_rects):
                    if rect.collidepoint(event.pos):
                        self.selected_slot_idx = idx
                        slot_num = idx + 1
                        if self.saves[idx] is not None:
                            return {"action": "load_slot", "slot": slot_num}
                        self.selected_save_slot = slot_num
                        self.screen_mode = "character_select"
                        return None

                if self.save_back_button_rect.collidepoint(event.pos):
                    self.screen_mode = "main"
                    return None

            return None

        # Seleção de personagem
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.screen_mode = "save_select"
                return None
            if event.key in (pygame.K_LEFT, pygame.K_a):
                self.selected_idx = (self.selected_idx - 1) % len(self.characters)
            elif event.key in (pygame.K_RIGHT, pygame.K_d):
                self.selected_idx = (self.selected_idx + 1) % len(self.characters)
            elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                self.screen_mode = "character_detail"
                self.detail_selected_btn = 0
                return None

        elif event.type == pygame.MOUSEMOTION:
            for idx, rect in enumerate(self.card_rects):
                if rect.collidepoint(event.pos):
                    self.selected_idx = idx
                    break

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for idx, rect in enumerate(self.card_rects):
                if rect.collidepoint(event.pos):
                    self.selected_idx = idx
                    self.screen_mode = "character_detail"
                    self.detail_selected_btn = 0
                    return None

            if self.start_button_rect.collidepoint(event.pos):
                self.screen_mode = "character_detail"
                self.detail_selected_btn = 0
                return None

            if self.back_button_rect.collidepoint(event.pos):
                self.screen_mode = "save_select"
                return None

        return None

    def _handle_character_detail_event(self, event: pygame.event.Event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.screen_mode = "character_select"
                return None
            if event.key in (
                pygame.K_LEFT,
                pygame.K_a,
                pygame.K_RIGHT,
                pygame.K_d,
                pygame.K_UP,
                pygame.K_w,
                pygame.K_DOWN,
                pygame.K_s,
            ):
                self.detail_selected_btn = 1 - self.detail_selected_btn
            elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                if self.detail_selected_btn == 0:
                    return {
                        "action": "new_game",
                        "character": self.characters[self.selected_idx],
                        "slot": self.selected_save_slot,
                    }
                self.screen_mode = "character_select"
                return None

        elif event.type == pygame.MOUSEMOTION:
            if self.detail_start_rect.collidepoint(event.pos):
                self.detail_selected_btn = 0
            elif self.detail_back_rect.collidepoint(event.pos):
                self.detail_selected_btn = 1

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.detail_start_rect.collidepoint(event.pos):
                return {
                    "action": "new_game",
                    "character": self.characters[self.selected_idx],
                    "slot": self.selected_save_slot,
                }
            if self.detail_back_rect.collidepoint(event.pos):
                self.screen_mode = "character_select"
                return None

        return None

    def draw(self):
        self._update_layout()

        if self.screen_mode == "settings":
            self.settings_menu.draw(overlay_mode=False)
            pygame.display.update()
            return

        now = pygame.time.get_ticks()
        if now - self.last_anim_update >= self.ANIMATION_COOLDOWN:
            self.frame_index = (self.frame_index + 1) % self.FRAMES_COUNT
            self.last_anim_update = now

        screen_w = self.surface.get_width()
        screen_h = self.surface.get_height()

        self.surface.fill((14, 16, 24))

        title_surf = self.title_font.render(
            "ROGUELIKE PROCEDURAL", True, (245, 245, 250)
        )
        title_rect = title_surf.get_rect(center=(screen_w // 2, 56))
        self.surface.blit(title_surf, title_rect)

        if self.screen_mode == "main":
            self._draw_main_screen(screen_w, screen_h)
        elif self.screen_mode == "save_select":
            self._draw_save_select_screen(screen_w, screen_h)
        elif self.screen_mode == "character_detail":
            self._draw_character_detail_screen(screen_w, screen_h)
        else:
            self._draw_character_select_screen(screen_w, screen_h)

        pygame.display.update()

    def _draw_main_screen(self, screen_w: int, screen_h: int):
        subtitle_surf = self.subtitle_font.render(
            "Menu Principal", True, (170, 178, 200)
        )
        subtitle_rect = subtitle_surf.get_rect(center=(screen_w // 2, 105))
        self.surface.blit(subtitle_surf, subtitle_rect)

        for idx, opt in enumerate(self.main_options):
            rect = self.main_button_rects[idx]
            enabled = opt["enabled"]
            is_selected = idx == self.main_selected_idx and enabled

            if not enabled:
                bg_color = (20, 22, 30)
                border_color = (45, 48, 62)
                label_color = (90, 95, 110)
                sub_color = (75, 80, 95)
                border_width = 2
            elif is_selected:
                bg_color = (34, 42, 62)
                border_color = (15, 227, 208)
                label_color = (255, 255, 255)
                sub_color = (15, 227, 208)
                border_width = 3
            else:
                bg_color = (24, 28, 40)
                border_color = (70, 78, 102)
                label_color = (215, 220, 232)
                sub_color = (150, 158, 180)
                border_width = 2

            pygame.draw.rect(
                self.surface,
                bg_color,
                rect,
                border_radius=12,
            )
            pygame.draw.rect(
                self.surface,
                border_color,
                rect,
                width=border_width,
                border_radius=12,
            )

            label_surf = self.subtitle_font.render(opt["label"], True, label_color)
            if opt["subtitle"]:
                label_rect = label_surf.get_rect(center=(rect.centerx, rect.centery - 10))
                self.surface.blit(label_surf, label_rect)

                sub_surf = self.hint_font.render(opt["subtitle"], True, sub_color)
                sub_rect = sub_surf.get_rect(center=(rect.centerx, rect.centery + 15))
                self.surface.blit(sub_surf, sub_rect)
            else:
                if opt["id"] == "continue" and not enabled:
                    label_rect = label_surf.get_rect(center=(rect.centerx, rect.centery - 10))
                    self.surface.blit(label_surf, label_rect)
                    no_save_surf = self.hint_font.render(
                        "Nenhum jogo salvo encontrado", True, sub_color
                    )
                    no_save_rect = no_save_surf.get_rect(center=(rect.centerx, rect.centery + 15))
                    self.surface.blit(no_save_surf, no_save_rect)
                else:
                    label_rect = label_surf.get_rect(center=rect.center)
                    self.surface.blit(label_surf, label_rect)

        hint_surf = self.hint_font.render(
            "[W / S ou Setas] Navegar    |    [ENTER ou Clique] Confirmar",
            True,
            (140, 148, 170),
        )
        hint_rect = hint_surf.get_rect(center=(screen_w // 2, screen_h - 24))
        self.surface.blit(hint_surf, hint_rect)

    def _draw_save_select_screen(self, screen_w: int, screen_h: int):
        subtitle_surf = self.subtitle_font.render(
            "Selecione um Slot de Save", True, (170, 178, 200)
        )
        subtitle_rect = subtitle_surf.get_rect(center=(screen_w // 2, 102))
        self.surface.blit(subtitle_surf, subtitle_rect)

        mouse_pos = pygame.mouse.get_pos()

        for idx, save_data in enumerate(self.saves):
            rect = self.save_card_rects[idx]
            is_selected = idx == self.selected_slot_idx

            if save_data is None:
                accent = (15, 227, 208)
                bg_color = (26, 30, 44) if is_selected else (20, 23, 33)
                border_color = accent if is_selected else (60, 68, 90)
            else:
                char_info = save_data.get("character", {})
                accent = tuple(char_info.get("accent_color", (15, 227, 208)))
                bg_color = (30, 35, 50) if is_selected else (22, 25, 36)
                border_color = accent if is_selected else (65, 72, 95)

            pygame.draw.rect(self.surface, bg_color, rect, border_radius=14)
            pygame.draw.rect(
                self.surface,
                border_color,
                rect,
                width=4 if is_selected else 2,
                border_radius=14,
            )

            slot_title = self.card_font.render(
                f"SLOT {idx + 1}", True, accent if is_selected else (190, 198, 215)
            )
            self.surface.blit(
                slot_title, slot_title.get_rect(center=(rect.centerx, rect.y + 24))
            )

            if save_data is None:
                empty_surf = self.subtitle_font.render("VAZIO", True, (130, 138, 160))
                self.surface.blit(
                    empty_surf,
                    empty_surf.get_rect(center=(rect.centerx, rect.centery - 10)),
                )
                new_surf = self.hint_font.render(
                    "Novo Jogo", True, accent if is_selected else (110, 118, 140)
                )
                self.surface.blit(
                    new_surf,
                    new_surf.get_rect(center=(rect.centerx, rect.centery + 22)),
                )
            else:
                char_info = save_data.get("character", {})
                char_id = char_info.get("id")
                char_idx = next(
                    (i for i, c in enumerate(self.characters) if c["id"] == char_id),
                    0,
                )

                inner_rect = pygame.Rect(rect.x + 24, rect.y + 44, rect.width - 48, 128)
                pygame.draw.rect(
                    self.surface, (16, 18, 28), inner_rect, border_radius=10
                )

                frame_idx = self.frame_index if is_selected else 0
                sprite = self.previews[char_idx][frame_idx]
                self.surface.blit(sprite, sprite.get_rect(center=inner_rect.center))

                char_name = char_info.get("name", "Personagem")
                name_surf = self.card_font.render(char_name, True, (235, 240, 248))
                self.surface.blit(
                    name_surf,
                    name_surf.get_rect(center=(rect.centerx, rect.bottom - 90)),
                )

                lvl = save_data.get("world", {}).get("current_level_idx", 0) + 1
                lvl_surf = self.hint_font.render(f"Fase {lvl}", True, accent)
                self.surface.blit(
                    lvl_surf,
                    lvl_surf.get_rect(center=(rect.centerx, rect.bottom - 62)),
                )

                del_rect = self.delete_button_rects[idx]
                del_hover = del_rect.collidepoint(mouse_pos)
                del_bg = (165, 45, 55) if del_hover else (95, 32, 38)
                pygame.draw.rect(self.surface, del_bg, del_rect, border_radius=8)
                pygame.draw.rect(
                    self.surface, (215, 80, 90), del_rect, width=1, border_radius=8
                )
                del_surf = self.hint_font.render("EXCLUIR", True, (250, 235, 235))
                self.surface.blit(del_surf, del_surf.get_rect(center=del_rect.center))

        # Botão Voltar
        pygame.draw.rect(
            self.surface,
            (38, 43, 60),
            self.save_back_button_rect,
            border_radius=10,
        )
        pygame.draw.rect(
            self.surface,
            (95, 105, 130),
            self.save_back_button_rect,
            width=2,
            border_radius=10,
        )
        back_text = self.subtitle_font.render("VOLTAR", True, (220, 225, 235))
        self.surface.blit(
            back_text, back_text.get_rect(center=self.save_back_button_rect.center)
        )

        hint_surf = self.hint_font.render(
            "[A/D] Selecionar Slot   |   [ENTER/Clique] Jogar   |   [DEL] Excluir   |   [ESC] Voltar",
            True,
            (140, 148, 170),
        )
        self.surface.blit(
            hint_surf, hint_surf.get_rect(center=(screen_w // 2, screen_h - 22))
        )

    def _draw_character_select_screen(self, screen_w: int, screen_h: int):
        subtitle_surf = self.subtitle_font.render(
            "Escolha seu Personagem", True, (170, 178, 200)
        )
        subtitle_rect = subtitle_surf.get_rect(center=(screen_w // 2, 102))
        self.surface.blit(subtitle_surf, subtitle_rect)

        for idx, char in enumerate(self.characters):
            rect = self.card_rects[idx]
            is_selected = idx == self.selected_idx
            accent = char["accent_color"]

            bg_color = (30, 35, 50) if is_selected else (22, 25, 36)
            border_color = accent if is_selected else (65, 72, 95)
            border_width = 4 if is_selected else 2

            pygame.draw.rect(
                self.surface,
                bg_color,
                rect,
                border_radius=14,
            )
            pygame.draw.rect(
                self.surface,
                border_color,
                rect,
                width=border_width,
                border_radius=14,
            )

            inner_h = max(110, rect.height - 105)
            inner_rect = pygame.Rect(
                rect.x + 20,
                rect.y + 18,
                rect.width - 40,
                inner_h,
            )
            pygame.draw.rect(
                self.surface,
                (16, 18, 28),
                inner_rect,
                border_radius=10,
            )

            frame_idx = self.frame_index if is_selected else 0
            sprite = self.previews[idx][frame_idx]
            sprite_rect = sprite.get_rect(center=inner_rect.center)
            self.surface.blit(sprite, sprite_rect)

            name_color = accent if is_selected else (210, 215, 225)
            name_surf = self.card_font.render(char["name"], True, name_color)
            name_rect = name_surf.get_rect(
                center=(rect.centerx, rect.bottom - 44)
            )
            self.surface.blit(name_surf, name_rect)

            if is_selected:
                tag_surf = self.hint_font.render("SELECIONADO", True, (240, 240, 245))
                tag_rect = tag_surf.get_rect(
                    center=(rect.centerx, rect.bottom - 18)
                )
                self.surface.blit(tag_surf, tag_rect)

        pygame.draw.rect(
            self.surface,
            (38, 43, 60),
            self.back_button_rect,
            border_radius=10,
        )
        pygame.draw.rect(
            self.surface,
            (95, 105, 130),
            self.back_button_rect,
            width=2,
            border_radius=10,
        )
        back_text = self.subtitle_font.render("VOLTAR", True, (220, 225, 235))
        back_rect = back_text.get_rect(center=self.back_button_rect.center)
        self.surface.blit(back_text, back_rect)

        selected_accent = self.characters[self.selected_idx]["accent_color"]
        pygame.draw.rect(
            self.surface,
            selected_accent,
            self.start_button_rect,
            border_radius=10,
        )
        btn_text = self.subtitle_font.render("INICIAR JOGO", True, (12, 14, 20))
        btn_rect = btn_text.get_rect(center=self.start_button_rect.center)
        self.surface.blit(btn_text, btn_rect)

        hint_surf = self.hint_font.render(
            "[A / D ou Setas] Selecionar   |   [ENTER] Avançar   |   [ESC] Voltar",
            True,
            (140, 148, 170),
        )
        hint_rect = hint_surf.get_rect(center=(screen_w // 2, screen_h - 22))
        self.surface.blit(hint_surf, hint_rect)

    def _wrap_text(self, text: str, font: pygame.font.Font, max_width: int) -> list:
        words = text.split()
        lines = []
        current = ""
        for word in words:
            test = f"{current} {word}".strip()
            if font.size(test)[0] <= max_width:
                current = test
            else:
                if current:
                    lines.append(current)
                current = word
        if current:
            lines.append(current)
        return lines

    def _draw_character_detail_screen(self, screen_w: int, screen_h: int):
        char = self.characters[self.selected_idx]
        accent = char["accent_color"]

        panel_w = min(820, screen_w - 60)
        panel_h = min(500, screen_h - 150)
        panel_rect = pygame.Rect(
            (screen_w - panel_w) // 2,
            100,
            panel_w,
            panel_h,
        )
        pygame.draw.rect(self.surface, (22, 26, 38), panel_rect, border_radius=14)
        pygame.draw.rect(self.surface, accent, panel_rect, width=2, border_radius=14)

        # Sprite do personagem à esquerda
        frames = self.previews[self.selected_idx] if self.selected_idx < len(self.previews) else []
        sprite_box = pygame.Rect(panel_rect.left + 28, panel_rect.top + 28, 120, 120)
        pygame.draw.rect(self.surface, (16, 19, 28), sprite_box, border_radius=10)
        pygame.draw.rect(self.surface, accent, sprite_box, width=2, border_radius=10)
        if frames:
            sprite = frames[self.frame_index % len(frames)]
            scaled = pygame.transform.scale(sprite, (96, 96))
            self.surface.blit(scaled, scaled.get_rect(center=sprite_box.center))

        # Título e citação ao lado do sprite
        text_left = sprite_box.right + 24
        text_max_w = panel_rect.right - 28 - text_left

        title_surf = self.subtitle_font.render(
            char.get("title", char["name"]), True, accent
        )
        self.surface.blit(title_surf, (text_left, panel_rect.top + 28))

        y_cursor = panel_rect.top + 66
        for line in self._wrap_text(char.get("quote", ""), self.hint_font, text_max_w):
            q_surf = self.hint_font.render(line, True, (200, 208, 225))
            self.surface.blit(q_surf, (text_left, y_cursor))
            y_cursor += 22

        # História (lore) abaixo do bloco superior
        lore_top = max(sprite_box.bottom + 22, y_cursor + 12)
        lore_max_w = panel_rect.width - 56
        for line in self._wrap_text(char.get("lore", ""), self.hint_font, lore_max_w):
            if lore_top > panel_rect.bottom - 115:
                break
            l_surf = self.hint_font.render(line, True, (225, 230, 240))
            self.surface.blit(l_surf, (panel_rect.left + 28, lore_top))
            lore_top += 24

        # Afinidade e Fraqueza
        affinity = char.get("affinity", "-")
        weakness = char.get("weakness", "-")
        stats_surf = self.hint_font.render(
            f"Afinidade: {affinity}   |   Fraqueza: {weakness}",
            True,
            accent,
        )
        self.surface.blit(
            stats_surf,
            stats_surf.get_rect(center=(panel_rect.centerx, panel_rect.bottom - 88)),
        )

        # Botões Voltar e Iniciar Jogo
        btn_y = panel_rect.bottom - 64
        self.detail_back_rect = pygame.Rect(panel_rect.centerx - 230, btn_y, 200, 46)
        self.detail_start_rect = pygame.Rect(panel_rect.centerx + 30, btn_y, 200, 46)

        back_sel = self.detail_selected_btn == 1
        pygame.draw.rect(
            self.surface,
            (46, 52, 72) if back_sel else (32, 36, 50),
            self.detail_back_rect,
            border_radius=10,
        )
        pygame.draw.rect(
            self.surface,
            accent if back_sel else (80, 88, 110),
            self.detail_back_rect,
            width=2,
            border_radius=10,
        )
        back_lbl = self.subtitle_font.render("VOLTAR", True, (230, 235, 245))
        self.surface.blit(back_lbl, back_lbl.get_rect(center=self.detail_back_rect.center))

        start_sel = self.detail_selected_btn == 0
        pygame.draw.rect(
            self.surface,
            accent if start_sel else (32, 36, 50),
            self.detail_start_rect,
            border_radius=10,
        )
        pygame.draw.rect(
            self.surface,
            accent,
            self.detail_start_rect,
            width=2,
            border_radius=10,
        )
        start_lbl = self.subtitle_font.render(
            "INICIAR", True, (12, 14, 20) if start_sel else (230, 235, 245)
        )
        self.surface.blit(
            start_lbl, start_lbl.get_rect(center=self.detail_start_rect.center)
        )

        hint_surf = self.hint_font.render(
            "[A / D] Alternar   |   [ENTER] Confirmar   |   [ESC] Voltar",
            True,
            (140, 148, 170),
        )
        self.surface.blit(
            hint_surf, hint_surf.get_rect(center=(screen_w // 2, screen_h - 22))
        )
