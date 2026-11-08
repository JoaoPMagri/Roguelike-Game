from entities import player
import random
import sys
import pygame
from pygame.locals import QUIT

from config import WIDTH, HEIGHT, FPS, TILE_SIZE
from entities import Player
from collisions import CollisionManager
from rendering import GameRenderer, Camera
from maps_generator import MapService


class Game:
    def __init__(self):
        pygame.init()

        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption(
            'Mapas com Geração Procedural - Roguelike'
        )
        self.clock = pygame.time.Clock()

        self.renderer = GameRenderer(self.screen)
        self.camera = Camera()
        self.collision_manager = CollisionManager()
        self.player = Player()

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

        self.entrance_door = None
        self.exit_door = None

        # Cada entrada representa um nível puro ou intermediário.
        self.levels_history = []
        self.current_level_idx = -1
        self.map_view_dismissed = False

        self._start_game()

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

    def _start_game(self):
        """Cria o primeiro mapa puro da partida."""
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

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()

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
            collision_walls
        ):
            self.player.set_position(target_x, target_y)

        current_player_rect = self.player.get_rect()

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
            self.clock.tick(FPS)
            self.handle_events()

            keys = pygame.key.get_pressed()
            self.update_player(keys)
            self.camera.update(self.player.x, self.player.y)

            if not keys[pygame.K_TAB]:
                self.map_view_dismissed = False
                show_full_map = False
            else:
                if self.player.is_moving:
                    self.map_view_dismissed = True
                show_full_map = not self.map_view_dismissed

            self.renderer.render_frame(
                self.floors,
                self.walls,
                self.player,
                self.exit_door,
                self.entrance_door,
                self.current_level_idx,
                self.levels_history[self.current_level_idx],
                self.camera,
                show_full_map=show_full_map
            )

if __name__ == "__main__":
    game = Game()
    game.run()
