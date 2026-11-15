from entities import player
import random
import sys
import pygame
from pygame.locals import QUIT

from config import WIDTH, HEIGHT, FPS, TILE_SIZE, CHARACTER_OPTIONS, EFFECT_DURATION_MS
from entities import Player
from collisions import CollisionManager
from rendering import GameRenderer, Camera, StartMenu, PauseMenu, SettingsMenu
from maps_generator import MapService
from persistence import SaveManager


class Game:
    def __init__(self):
        pygame.init()

        saved_settings = SaveManager.load_settings(WIDTH, HEIGHT, FPS)
        self.window_width = saved_settings["width"]
        self.window_height = saved_settings["height"]
        self.fps = saved_settings["fps"]

        self.screen = pygame.display.set_mode((self.window_width, self.window_height))
        pygame.display.set_caption(
            'Mapas com Geração Procedural - Roguelike'
        )
        self.clock = pygame.time.Clock()

        self.renderer = GameRenderer(self.screen)
        self.settings_menu = SettingsMenu(
            self.screen,
            current_width=self.window_width,
            current_height=self.window_height,
            current_fps=self.fps,
        )
        self.menu = StartMenu(
            self.screen,
            settings_menu=self.settings_menu,
            saves=SaveManager.list_saves(),
        )
        self.pause_menu = PauseMenu(self.screen, self.settings_menu)
        self.camera = Camera(
            viewport_width=self.window_width,
            viewport_height=self.window_height,
        )
        self.collision_manager = CollisionManager()
        self.player = Player()
        self.state = "menu"
        self.selected_character = None
        self.current_save_slot = 1

        self.master_seed = random.random()
        self.rng = random.Random(self.master_seed)

        # Algoritmos disponíveis no ciclo atual.
        # 0 = Random Walk
        # 1 = Cellular Automata
        # 2 = BSP
        # 3 = Hybrid
        self.available_map_types = [0, 1, 2, 3]

        self.floors = []
        self.walls = []
        self.obstacles = []
        self.obstacle_effects = []
        self.active_screen_effect = None
        self.effect_expires_at = 0

        self.entrance_door = None
        self.exit_door = None

        # Cada entrada representa um nível puro ou intermediário.
        self.levels_history = []
        self.current_level_idx = -1
        self.map_view_dismissed = False
        self.map_preview_idx = None
        self.preview_data = None
        self.map_transition = None

    def _get_next_map_type(self, exclude=None):
        """
        Sorteia um algoritmo sem repetição dentro do ciclo atual.

        Ao iniciar um novo ciclo, o algoritmo que encerrou o ciclo
        anterior é excluído do primeiro sorteio.
        """
        if not self.available_map_types:
            self.available_map_types = [0, 1, 2, 3]

            if exclude is not None:
                self.available_map_types.remove(exclude)

        index = self.rng.randrange(len(self.available_map_types))
        map_type = self.available_map_types.pop(index)

        print("Novo algoritmo puro:", map_type)
        return map_type

    def _start_game(self, initial_map_type=None):
        """Cria o primeiro mapa puro da partida (usando o mapa tema do personagem, se informado)."""
        self.master_seed = random.random()
        self.rng = random.Random(self.master_seed)
        self.available_map_types = [0, 1, 2, 3]
        self.levels_history.clear()
        self.renderer.explored_tiles_by_level.clear()
        self.renderer.transition_mask.clear()

        if initial_map_type is not None and initial_map_type in self.available_map_types:
            self.available_map_types.remove(initial_map_type)
            map_type = initial_map_type
            print("Novo algoritmo puro (tema do personagem):", map_type)
        else:
            map_type = self._get_next_map_type()

        seed = self.rng.random()

        self.current_level_idx = 0

        # No primeiro mapa não existe porta de entrada: existe apenas
        # uma posição inicial. A saída continua sendo uma porta normal.
        sides = ["top", "bottom", "left", "right"]
        spawn_side = self.rng.choice(sides)
        exit_side = self.rng.choice([
            side for side in sides
            if side != spawn_side
        ])

        self.levels_history.append({
            "type": "pure",
            "algorithm": map_type,
            "seed": seed,
            "entrance_side": None,
            "spawn_side": spawn_side,
            "exit_side": exit_side
        })

        self._generate_and_apply_pure_map(
            seed,
            map_type,
            spawn_mode="initial",
            entrance_side=None,
            exit_side=exit_side,
            spawn_side=spawn_side
        )
        self.save_current_game()

    def save_current_game(self):
        """Persiste o estado atual da partida localmente no slot ativo."""
        if self.selected_character is None or not self.levels_history:
            return
        SaveManager.save_game(
            selected_character=self.selected_character,
            player=self.player,
            master_seed=self.master_seed,
            available_map_types=self.available_map_types,
            levels_history=self.levels_history,
            current_level_idx=self.current_level_idx,
            explored_tiles_by_level=self.renderer.explored_tiles_by_level,
            slot=self.current_save_slot,
        )

    def load_saved_game(self, slot: int = 1) -> bool:
        """Restaura uma partida salva localmente do slot informado."""
        save_data = SaveManager.load_game(slot)
        if not save_data:
            return False

        saved_char = save_data.get("character") or CHARACTER_OPTIONS[0]
        # Garante compatibilidade com as opções atuais de personagem
        char_id = saved_char.get("id")
        matched_char = next(
            (c for c in CHARACTER_OPTIONS if c["id"] == char_id),
            saved_char,
        )
        self.selected_character = matched_char
        self.renderer.set_player_sprite(matched_char["sprite_path"])
        self.renderer.set_player_theme(matched_char.get("theme_map", 0))

        world = save_data["world"]
        self.master_seed = world.get("master_seed", random.random())
        self.rng = random.Random(self.master_seed)
        self.available_map_types = list(world.get("available_map_types", [0, 1, 2, 3]))
        self.levels_history = list(world.get("levels_history", []))
        self.current_level_idx = int(world.get("current_level_idx", 0))

        if not self.levels_history or not (0 <= self.current_level_idx < len(self.levels_history)):
            return False

        self.renderer.transition_mask.clear()
        self.renderer.explored_tiles_by_level.clear()

        raw_explored = world.get("explored_tiles_by_level", {})
        for lvl_str, coords in raw_explored.items():
            try:
                lvl_idx = int(lvl_str)
                self.renderer.explored_tiles_by_level[lvl_idx] = {
                    (int(pos[0]), int(pos[1])) for pos in coords
                }
            except (ValueError, TypeError):
                continue

        current_level = self.levels_history[self.current_level_idx]
        self._load_level(current_level, spawn_mode=None)

        player_data = save_data["player"]
        self.player.set_position(
            float(player_data.get("x", self.player.x)),
            float(player_data.get("y", self.player.y)),
        )
        self.player.direction = player_data.get("direction", "down")
        self.camera.update(self.player.x, self.player.y)

        return True

    def _apply_map(
        self,
        mapa,
        seed,
        spawn_mode=None,
        spawn_info=None,
        entrance_side=None,
        exit_side=None,
        spawn_side=None
    ):
        """Carrega o mapa, suas portas e posiciona o jogador."""

        (
            self.floors,
            self.walls,
            self.obstacles,
            self.obstacle_effects,
            self.entrance_door,
            self.exit_door,
            spawn_position
        ) = MapService.load_geometry(
            mapa,
            TILE_SIZE,
            seed,
            spawn_info=spawn_info,
            entrance_side=entrance_side,
            exit_side=exit_side,
            spawn_side=spawn_side
        )

        # -----------------------------------------
        # Posicionamento do jogador
        # -----------------------------------------

        spawn_tile = None

        if spawn_mode == "entrance" and self.entrance_door is not None:
            spawn_tile = self.entrance_door["floor"]

        elif spawn_mode == "exit" and self.exit_door is not None:
            spawn_tile = self.exit_door["floor"]

        elif spawn_mode == "initial":
            spawn_tile = spawn_position

        if spawn_tile is not None:
            floor_x, floor_y = spawn_tile
            self.player.set_position(
                floor_x + TILE_SIZE / 2,
                floor_y + TILE_SIZE / 2
            )

        self.camera.set_map_size(
            mapa.width * TILE_SIZE,
            mapa.height * TILE_SIZE
        )
        self.camera.update(self.player.x, self.player.y)

    def _generate_and_apply_pure_map(
        self,
        seed,
        map_type,
        spawn_mode=None,
        entrance_side=None,
        exit_side=None,
        spawn_side=None
    ):
        mapa = MapService.generate_map(
            map_type,
            seed
        )

        # Se a saída ainda não foi definida,
        # escolhe um lado diferente da entrada.
        if exit_side is None:
            sides = [
                "top",
                "bottom",
                "left",
                "right"
            ]

            if entrance_side is not None:
                sides.remove(entrance_side)

            exit_side = self.rng.choice(sides)

        self._apply_map(
            mapa,
            seed=seed,
            spawn_mode=spawn_mode,
            entrance_side=entrance_side,
            exit_side=exit_side,
            spawn_side=spawn_side
        )

    def _generate_and_apply_intermediate_map(
        self,
        level,
        spawn_mode
    ):
        """Regenera um mapa intermediário usando os dados salvos."""

        mapa, spawn_info = MapService.generate_intermediate_map(
            algorithm_a=level["algorithm_a"],
            algorithm_b=level["algorithm_b"],
            seed_a=level["seed_a"],
            seed_b=level["seed_b"],
            layout=level["layout"],
            reverse=level["reverse"]
        )

        geometry_seed = level["geometry_seed"]

        self._apply_map(
            mapa,
            seed=geometry_seed,
            spawn_mode=spawn_mode,
            spawn_info=spawn_info,
            entrance_side=level.get("entrance_side"),
            exit_side=level.get("exit_side")
        )

    def _create_intermediate_level(self, current_level):
        """
        Cria uma ponte entre o mapa puro atual e o próximo algoritmo.

        O algoritmo A é o mapa atual.
        O algoritmo B é sorteado do ciclo atual.
        """
        algorithm_a = current_level["algorithm"]
        algorithm_b = self._get_next_map_type(
            exclude=algorithm_a
        )

        # A primeira parte usa a seed do mapa puro atual.
        seed_a = current_level["seed"]

        # A segunda parte recebe uma nova seed independente.
        seed_b = self.rng.random()

        # A composição do intermediário precisa preservar a continuidade
        # espacial do mapa anterior. O submapa A representa o mapa de
        # origem, enquanto o submapa B representa o próximo algoritmo.
        #
        # Por isso, a orientação não pode ser completamente aleatória:
        # ela é definida pela direção da saída do mapa anterior.
        #
        # Exemplo:
        #   saída anterior = direita
        #   entrada do intermediário = esquerda
        #   A fica à esquerda e B à direita
        #
        # Assim mantemos simultaneamente:
        # 1. entrada no lado oposto à saída anterior;
        # 2. entrada dentro do submapa de origem (A);
        # 3. saída dentro do novo submapa (B);
        # 4. continuidade espacial entre os mapas.
        previous_exit_side = current_level.get("exit_side")

        if previous_exit_side is None:
            # Fallback apenas para níveis antigos sem informação de lado.
            sides = ["top", "bottom", "left", "right"]
            entrance_side = self.rng.choice(sides)
            exit_side = self.rng.choice([
                side for side in sides
                if side != entrance_side
            ])
            layout = self.rng.choice(["horizontal", "vertical"])
            reverse = self.rng.choice([False, True])
        else:
            entrance_side = MapService.OPPOSITE_SIDES[
                previous_exit_side
            ]

            # A saída do intermediário continua na mesma direção da saída
            # do mapa de origem. Dessa forma, o jogador atravessa:
            # mapa A -> intermediário A -> intermediário B -> mapa B.
            exit_side = previous_exit_side

            if previous_exit_side in ("left", "right"):
                layout = "horizontal"

                # A deve ficar do lado da entrada e B do lado da saída.
                # left  -> A | B
                # right -> B | A
                reverse = previous_exit_side == "left"
            else:
                layout = "vertical"

                # A deve ficar do lado da entrada e B do lado da saída.
                # top    -> A / B
                # bottom -> B / A
                reverse = previous_exit_side == "top"

        # Seed utilizada somente para determinar a geometria das portas.
        geometry_seed = self.rng.random()

        return {
            "type": "intermediate",
            "algorithm_a": algorithm_a,
            "algorithm_b": algorithm_b,
            "seed_a": seed_a,
            "seed_b": seed_b,
            "layout": layout,
            "reverse": reverse,
            "geometry_seed": geometry_seed,
            "entrance_side": entrance_side,
            "exit_side": exit_side
        }

    def _create_next_pure_level(self, intermediate_level):
        """
        Cria o mapa puro que vem depois do intermediário.
        """

        previous_exit_side = intermediate_level.get(
            "exit_side"
        )

        entrance_side = MapService.OPPOSITE_SIDES[
            previous_exit_side
        ]

        return {
            "type": "pure",
            "algorithm": intermediate_level["algorithm_b"],
            "seed": intermediate_level["seed_b"],

            "entrance_side": entrance_side,
            "exit_side": self.rng.choice([
                side for side in ["top", "bottom", "left", "right"]
                if side != entrance_side
            ])
        }

    def _load_level(self, level, spawn_mode):
        """Carrega qualquer nível do histórico."""
        if level["type"] == "pure":
            self._generate_and_apply_pure_map(
                level["seed"],
                level["algorithm"],
                spawn_mode,
                entrance_side=level.get("entrance_side"),
                exit_side=level.get("exit_side"),
                spawn_side=level.get("spawn_side")
            )
        else:
            self._generate_and_apply_intermediate_map(
                level,
                spawn_mode
            )

    def go_to_next_level(self):
        """
        Avança para o próximo nível.

        Puro → cria intermediário.
        Intermediário → vai diretamente para o puro sorteado.
        Níveis já visitados são apenas reutilizados.
        """
        next_idx = self.current_level_idx + 1

        # ---------------------------------------------------------
        # O próximo nível já existe no histórico.
        # ---------------------------------------------------------
        if next_idx < len(self.levels_history):
            level = self.levels_history[next_idx]

        # ---------------------------------------------------------
        # Ainda não existe. O que fazer depende do nível atual.
        # ---------------------------------------------------------
        else:
            current_level = self.levels_history[self.current_level_idx]

            if current_level["type"] == "pure":
                # Puro → cria mapa intermediário.
                level = self._create_intermediate_level(current_level)

            else:
                # Intermediário → NÃO sorteia outro algoritmo.
                # Vai diretamente para o algoritmo B já definido.
                level = self._create_next_pure_level(current_level)

            self.levels_history.append(level)

        self.current_level_idx = next_idx

        self._load_level(
            level,
            spawn_mode="entrance"
        )

        self.save_current_game()
        self._print_level_info(level)

    def go_to_prev_level(self):
        """Recua para o nível anterior, sempre reutilizando o histórico."""
        if self.current_level_idx <= 0:
            return

        prev_idx = self.current_level_idx - 1
        level = self.levels_history[prev_idx]

        self.current_level_idx = prev_idx

        self._load_level(
            level,
            spawn_mode="exit"
        )

        self.save_current_game()
        self._print_level_info(level)

    def _print_level_info(self, level):
        """Mostra no terminal informações úteis para testar a progressão."""
        if level["type"] == "pure":
            print(
                f"Nível {self.current_level_idx}: "
                f"PURO - algoritmo {level['algorithm']}"
            )
        else:
            direction = "horizontal" if level["layout"] == "horizontal" else "vertical"
            order = (
                f"{level['algorithm_a']} -> {level['algorithm_b']}"
                if not level["reverse"]
                else f"{level['algorithm_b']} -> {level['algorithm_a']}"
            )

            print(
                f"Nível {self.current_level_idx}: "
                f"INTERMEDIÁRIO - {order} - {direction}"
            )

    def apply_settings(self, width: int, height: int, fps: int):
        """Aplica e persiste novas configurações de tamanho da janela e FPS."""
        self.window_width = int(width)
        self.window_height = int(height)
        self.fps = int(fps)

        self.screen = pygame.display.set_mode((self.window_width, self.window_height))
        self.renderer.set_surface(self.screen)
        self.menu.surface = self.screen
        self.pause_menu.surface = self.screen
        self.settings_menu.surface = self.screen

        self.camera.viewport_width = self.window_width
        self.camera.viewport_height = self.window_height
        self.camera.update(self.player.x, self.player.y)

        SaveManager.save_settings(self.window_width, self.window_height, self.fps)

    def _get_active_map_snapshot(self) -> dict:
        """Retorna os dados do mapa atualmente exibido no TAB para animar a transição."""
        if self.preview_data is not None:
            return {
                **self.preview_data,
                "idx": self.map_preview_idx,
                "draw_player_marker": False,
            }
        return {
            "floors": self.floors,
            "walls": self.walls,
            "obstacles": self.obstacles,
            "entrance_door": self.entrance_door,
            "exit_door": self.exit_door,
            "camera": self.camera,
            "level": self.levels_history[self.current_level_idx],
            "idx": self.current_level_idx,
            "draw_player_marker": True,
        }

    def _start_map_slide_transition(self, target_idx: int, direction: str):
        from_data = self._get_active_map_snapshot()
        self._load_preview_level(target_idx)
        to_data = self._get_active_map_snapshot()
        self.map_transition = {
            "from_data": from_data,
            "to_data": to_data,
            "direction": direction,
            "start_time": pygame.time.get_ticks(),
            "duration": 650,
        }

    def _load_preview_level(self, level_idx: int):
        """Carrega apenas a geometria de um nível do histórico para pré-visualização no TAB."""
        self.map_preview_idx = level_idx
        if level_idx == self.current_level_idx:
            self.preview_data = None
            return

        level = self.levels_history[level_idx]
        if level["type"] == "pure":
            mapa = MapService.generate_map(level["algorithm"], level["seed"])
            geometry_seed = level["seed"]
            spawn_info = None
        else:
            mapa, spawn_info = MapService.generate_intermediate_map(
                algorithm_a=level["algorithm_a"],
                algorithm_b=level["algorithm_b"],
                seed_a=level["seed_a"],
                seed_b=level["seed_b"],
                layout=level["layout"],
                reverse=level["reverse"],
            )
            geometry_seed = level["geometry_seed"]

        floors, walls, _, _, entrance_door, exit_door, _ = MapService.load_geometry(
            mapa,
            TILE_SIZE,
            geometry_seed,
            spawn_info=spawn_info,
            entrance_side=level.get("entrance_side"),
            exit_side=level.get("exit_side"),
            spawn_side=level.get("spawn_side"),
        )
        preview_camera = Camera(
            viewport_width=self.window_width,
            viewport_height=self.window_height,
            map_width=mapa.width * TILE_SIZE,
            map_height=mapa.height * TILE_SIZE,
        )
        self.preview_data = {
            "floors": floors,
            "walls": walls,
            "entrance_door": entrance_door,
            "exit_door": exit_door,
            "camera": preview_camera,
            "level": level,
        }

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == QUIT:
                if self.state in ("playing", "paused"):
                    self.save_current_game()
                pygame.quit()
                sys.exit()

            if self.state == "menu":
                menu_result = self.menu.handle_event(
                    event,
                    self.window_width,
                    self.window_height,
                    self.fps,
                )
                if menu_result is not None:
                    action = menu_result.get("action")
                    if action == "load_slot":
                        slot = menu_result["slot"]
                        self.current_save_slot = slot
                        if self.load_saved_game(slot):
                            self.state = "playing"
                    elif action == "delete_slot":
                        SaveManager.delete_save(menu_result["slot"])
                        self.menu.refresh_saves(
                            SaveManager.list_saves(), reset_to_main=False
                        )
                    elif action == "new_game":
                        chosen_character = menu_result["character"]
                        self.current_save_slot = menu_result.get("slot", 1)
                        self.selected_character = chosen_character
                        self.renderer.set_player_sprite(chosen_character["sprite_path"])
                        self.renderer.set_player_theme(chosen_character.get("theme_map", 0))
                        self._start_game(initial_map_type=chosen_character.get("theme_map"))
                        self.state = "playing"
                    elif action == "apply_settings":
                        self.apply_settings(
                            menu_result["width"],
                            menu_result["height"],
                            menu_result["fps"],
                        )
                    elif action == "quit":
                        pygame.quit()
                        sys.exit()

            elif self.state == "playing":
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.pause_menu.reset()
                        self.state = "paused"
                    elif pygame.key.get_pressed()[pygame.K_TAB]:
                        key_to_side = {
                            pygame.K_w: "top",
                            pygame.K_UP: "top",
                            pygame.K_s: "bottom",
                            pygame.K_DOWN: "bottom",
                            pygame.K_a: "left",
                            pygame.K_LEFT: "left",
                            pygame.K_d: "right",
                            pygame.K_RIGHT: "right",
                        }
                        chosen_side = key_to_side.get(event.key)
                        if chosen_side is not None:
                            active_idx = (
                                self.map_preview_idx
                                if self.map_preview_idx is not None
                                else self.current_level_idx
                            )
                            active_entrance = (
                                self.preview_data["entrance_door"]
                                if self.preview_data is not None
                                else self.entrance_door
                            )
                            active_exit = (
                                self.preview_data["exit_door"]
                                if self.preview_data is not None
                                else self.exit_door
                            )
                            if (
                                active_entrance is not None
                                and chosen_side == active_entrance.get("side")
                                and active_idx > 0
                            ):
                                self._start_map_slide_transition(active_idx - 1, chosen_side)
                            elif (
                                active_exit is not None
                                and chosen_side == active_exit.get("side")
                                and active_idx + 1 < len(self.levels_history)
                            ):
                                self._start_map_slide_transition(active_idx + 1, chosen_side)

            elif self.state == "paused":
                pause_result = self.pause_menu.handle_event(
                    event,
                    self.window_width,
                    self.window_height,
                    self.fps,
                )
                if pause_result is not None:
                    action = pause_result.get("action")
                    if action == "resume":
                        self.state = "playing"
                    elif action == "apply_settings":
                        self.apply_settings(
                            pause_result["width"],
                            pause_result["height"],
                            pause_result["fps"],
                        )
                    elif action == "main_menu":
                        self.save_current_game()
                        self.menu.refresh_saves(SaveManager.list_saves())
                        self.state = "menu"

    def update_player(self, keys):
        target_x, target_y = self.player.calculate_desired_position(keys)
        candidate_rect = self.player.get_rect(target_x, target_y)

        # As portas ocupam um tile que normalmente seria parede,
        # mas precisam ser atravessáveis para disparar a transição.
        door_tiles = set()

        for door in (self.entrance_door, self.exit_door):
            if door is not None:
                door_tiles.add(door["tile"])

        collision_walls = [
            wall
            for wall in self.walls
            if (wall.x, wall.y) not in door_tiles
        ]

        if not self.collision_manager.check_wall_collision(
            candidate_rect,
            collision_walls + self.obstacles
        ):
            self.player.set_position(target_x, target_y)

        current_player_rect = self.player.get_rect()

        # Verifica contato do jogador com os efeitos ao redor dos obstáculos
        now = pygame.time.get_ticks()
        current_level = self.levels_history[self.current_level_idx]
        touching_effect = None
        for effect in self.obstacle_effects:
            if current_player_rect.colliderect(effect["rect"]):
                touching_effect = self.renderer.get_algorithm_at_rect(
                    effect.get("obstacle_rect", effect["rect"]),
                    self.camera,
                    current_level,
                )
                break

        if touching_effect is not None:
            self.active_screen_effect = touching_effect
            self.effect_expires_at = now + EFFECT_DURATION_MS
        elif self.active_screen_effect is not None and now >= self.effect_expires_at:
            self.active_screen_effect = None

        # =========================================================
        # EXIT → avança de nível
        # =========================================================

        if self.exit_door is not None:

            exit_x, exit_y = self.exit_door["tile"]

            exit_rect = pygame.Rect(
                exit_x,
                exit_y,
                TILE_SIZE,
                TILE_SIZE
            )

            touching_exit = self.collision_manager.check_trigger_collision(
                current_player_rect,
                exit_rect
            )

            if touching_exit:
                self.go_to_next_level()
                return

        # =========================================================
        # ENTRANCE → recua de nível
        # =========================================================

        if self.current_level_idx > 0 and self.entrance_door is not None:

            entrance_x, entrance_y = self.entrance_door["tile"]

            entrance_rect = pygame.Rect(
                entrance_x,
                entrance_y,
                TILE_SIZE,
                TILE_SIZE
            )

            touching_entrance = self.collision_manager.check_trigger_collision(
                current_player_rect,
                entrance_rect
            )

            if touching_entrance:
                self.go_to_prev_level()
                return

    def run(self):
        while True:
            self.clock.tick(self.fps)
            self.handle_events()

            if self.state == "menu":
                self.menu.draw()
                continue

            if self.state == "paused":
                self.renderer.render_frame(
                    self.floors,
                    self.walls,
                    self.player,
                    self.exit_door,
                    self.entrance_door,
                    self.current_level_idx,
                    self.levels_history[self.current_level_idx],
                    self.camera,
                    show_full_map=False,
                    flip_display=False,
                    obstacles=self.obstacles,
                    obstacle_effects=self.obstacle_effects,
                    active_screen_effect=self.active_screen_effect,
                )
                self.pause_menu.draw()
                continue

            keys = pygame.key.get_pressed()
            show_full_map = bool(keys[pygame.K_TAB])

            if not show_full_map:
                self.map_preview_idx = None
                self.preview_data = None
                self.map_transition = None
                self.update_player(keys)
            self.camera.update(self.player.x, self.player.y)

            if show_full_map and self.map_transition is not None:
                elapsed = pygame.time.get_ticks() - self.map_transition["start_time"]
                duration = self.map_transition["duration"]
                if elapsed < duration:
                    self.renderer.render_map_slide_transition(
                        self.map_transition["from_data"],
                        self.map_transition["to_data"],
                        self.map_transition["direction"],
                        elapsed / duration,
                        self.player,
                        self.current_level_idx,
                    )
                    continue
                self.map_transition = None

            if show_full_map and self.preview_data is not None:
                self.renderer.render_frame(
                    self.preview_data["floors"],
                    self.preview_data["walls"],
                    self.player,
                    self.preview_data["exit_door"],
                    self.preview_data["entrance_door"],
                    self.map_preview_idx,
                    self.preview_data["level"],
                    self.preview_data["camera"],
                    show_full_map=True,
                    draw_player_marker=False,
                )
            else:
                self.renderer.render_frame(
                    self.floors,
                    self.walls,
                    self.player,
                    self.exit_door,
                    self.entrance_door,
                    self.current_level_idx,
                    self.levels_history[self.current_level_idx],
                    self.camera,
                    show_full_map=show_full_map,
                    obstacles=self.obstacles,
                    obstacle_effects=self.obstacle_effects,
                    active_screen_effect=self.active_screen_effect,
                    draw_player_marker=True,
                )

if __name__ == "__main__":
    game = Game()
    game.run()
