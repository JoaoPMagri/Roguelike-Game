from entities import player
import random
import sys
import pygame
from pygame.locals import QUIT

from config import WIDTH, HEIGHT, FPS, TILE_SIZE
from entities import Player
from collisions import CollisionManager
from rendering import GameRenderer
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

        self.entrance_pos = (0.0, 0.0)
        self.exit_pos = (0.0, 0.0)

        self.entrance_triggered = False
        self.exit_triggered = False

        # Cada entrada representa um nível puro ou intermediário.
        self.levels_history = []
        self.current_level_idx = -1

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
        self.levels_history.append({
            "type": "pure",
            "algorithm": map_type,
            "seed": seed,
        })

        self._generate_and_apply_pure_map(
            seed,
            map_type,
            spawn_near_entrance=True
        )

    def _apply_map(
        self,
        mapa,
        seed: float,
        spawn_near_entrance: bool,
        spawn_info=None
    ):
        """Carrega a geometria do mapa e posiciona o jogador."""
        self.floors, self.walls, self.entrance_pos, self.exit_pos = MapService.load_geometry(
            mapa,
            TILE_SIZE,
            seed,
            spawn_info=spawn_info
        )

        if spawn_near_entrance:
            self.player.set_position(
                self.entrance_pos[0],
                self.entrance_pos[1]
            )

            # O jogador acabou de entrar pela entrance.
            self.entrance_triggered = True
            self.exit_triggered = False

        else:
            self.player.set_position(
                self.exit_pos[0],
                self.exit_pos[1]
            )

            # O jogador acabou de entrar pela exit.
            self.entrance_triggered = False
            self.exit_triggered = True

    def _generate_and_apply_pure_map(
        self,
        seed: float,
        map_type: int,
        spawn_near_entrance: bool
    ):
        mapa = MapService.generate_map(map_type, seed)
        self._apply_map(
            mapa,
            seed=seed,
            spawn_near_entrance=spawn_near_entrance
        )

    def _generate_and_apply_intermediate_map(self, level, spawn_near_entrance):
        """Regenera um mapa intermediário usando os dados salvos no histórico."""
        mapa, spawn_info = MapService.generate_intermediate_map(
            algorithm_a=level["algorithm_a"],
            algorithm_b=level["algorithm_b"],
            seed_a=level["seed_a"],
            seed_b=level["seed_b"],
            layout=level["layout"],
            reverse=level["reverse"],
        )

        # Usa uma seed própria e determinística para a escolha de entrance/exit.
        geometry_seed = level["geometry_seed"]

        self._apply_map(
            mapa,
            seed=geometry_seed,
            spawn_near_entrance=spawn_near_entrance,
            spawn_info=spawn_info
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

        # Define aleatoriamente a orientação da composição.
        layout = self.rng.choice(["horizontal", "vertical"])

        # Define aleatoriamente qual algoritmo ficará primeiro.
        reverse = self.rng.choice([False, True])

        # Seed utilizada somente para determinar entrance/exit da composição.
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
        }

    def _create_next_pure_level(self, intermediate_level):
        """
        Cria o mapa puro que vem depois de um intermediário.

        O mapa puro reutiliza a mesma seed usada para gerar o submapa B.
        Assim, o algoritmo sorteado para a transição é também o mapa puro
        que aparece logo depois dela, sem um novo sorteio de algoritmo.
        """
        return {
            "type": "pure",
            "algorithm": intermediate_level["algorithm_b"],
            "seed": intermediate_level["seed_b"],
        }

    def _load_level(self, level, spawn_near_entrance):
        """Carrega qualquer nível do histórico."""
        if level["type"] == "pure":
            self._generate_and_apply_pure_map(
                level["seed"],
                level["algorithm"],
                spawn_near_entrance
            )
        else:
            self._generate_and_apply_intermediate_map(
                level,
                spawn_near_entrance
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
            spawn_near_entrance=True
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
            spawn_near_entrance=False
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

        # Colisão com paredes
        if not self.collision_manager.check_wall_collision(
            candidate_rect,
            self.walls
        ):
            self.player.set_position(target_x, target_y)

        radius = self.player.radius
        trigger_size = radius * 2
        current_player_rect = self.player.get_rect()

        # =========================================================
        # EXIT → avança de nível
        # =========================================================

        exit_rect = pygame.Rect(
            self.exit_pos[0] - radius,
            self.exit_pos[1] - radius,
            trigger_size,
            trigger_size,
        )

        touching_exit = self.collision_manager.check_trigger_collision(
            current_player_rect,
            exit_rect
        )

        if not touching_exit:
            self.exit_triggered = False

        if touching_exit and not self.exit_triggered:
            self.exit_triggered = True
            self.go_to_next_level()
            return

        # =========================================================
        # ENTRANCE → recua de nível
        # =========================================================

        if self.current_level_idx >= 1:
            entrance_rect = pygame.Rect(
                self.entrance_pos[0] - radius,
                self.entrance_pos[1] - radius,
                trigger_size,
                trigger_size,
            )

            touching_entrance = self.collision_manager.check_trigger_collision(
                current_player_rect,
                entrance_rect
            )

            if not touching_entrance:
                self.entrance_triggered = False

            if touching_entrance and not self.entrance_triggered:
                self.entrance_triggered = True
                self.go_to_prev_level()
                return

    def run(self):
        while True:
            self.clock.tick(FPS)
            self.handle_events()

            keys = pygame.key.get_pressed()
            self.update_player(keys)

            self.renderer.render_frame(
                self.floors,
                self.walls,
                self.player,
                self.exit_pos,
                self.entrance_pos,
                self.current_level_idx,
                self.levels_history[self.current_level_idx]
            )

if __name__ == "__main__":
    game = Game()
    game.run()
