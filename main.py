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

        # Algoritmos disponíveis no ciclo atual
        self.available_map_types = [0, 1, 2, 3]

        self.floors = []
        self.walls = []

        self.entrance_pos = (0.0, 0.0)
        self.exit_pos = (0.0, 0.0)

        self.entrance_triggered = False
        self.exit_triggered = False

        # Histórico dos mapas visitados
        self.levels_history = []
        self.current_level_idx = -1

        self._start_game()

    def _get_next_map_type(self):
        """
        Retorna aleatoriamente um algoritmo do ciclo atual.

        Um algoritmo só pode voltar a ser escolhido depois que
        os outros três algoritmos do ciclo também tiverem sido usados.
        """

        if not self.available_map_types:
            self.available_map_types = [0, 1, 2, 3]

        index = self.rng.randrange(len(self.available_map_types))

        choose_map = self.available_map_types.pop(index)
        print("Mapa: ", choose_map)

        return choose_map
    
    def _start_game(self):
        map_type = self._get_next_map_type()
        seed = self.rng.random()

        self.current_level_idx = 0
        self.levels_history.append((seed, map_type))

        self._generate_and_apply_map(
            seed,
            map_type,
            spawn_near_entrance=True
        )

    def _apply_map(self, mapa, seed: float, spawn_near_entrance: bool):
        """
        Carrega geometria do mapa e posiciona o jogador.
        - spawn_near_entrance=True  → jogador nasce perto da ENTRANCE (bolinha branca)
          (ocorre quando o jogador avançou para este mapa pela bolinha preta do anterior)
        - spawn_near_entrance=False → jogador nasce perto da EXIT (bolinha preta)
          (ocorre quando o jogador recuou para este mapa pela bolinha branca do próximo)
        """
        self.floors, self.walls, self.entrance_pos, self.exit_pos = MapService.load_geometry(
            mapa, TILE_SIZE, seed
        )

        if spawn_near_entrance:
            self.player.set_position(
                self.entrance_pos[0],
                self.entrance_pos[1]
            )
            self.entrance_triggered = True
        else:
            self.player.set_position(
                self.exit_pos[0],
                self.exit_pos[1]
            )
            self.entrance_triggered = False
            self.exit_triggered = True

    def _generate_and_apply_map(self, seed: float, map_type: int, spawn_near_entrance: bool):
        mapa = MapService.generate_map(map_type, seed)
        self._apply_map(mapa, seed=seed, spawn_near_entrance=spawn_near_entrance)

    def change_map(self, map_type: int):
        """Chamado pelos atalhos de teclado — reseta o histórico e começa no tipo escolhido."""
        self.map_type = map_type
        new_seed = self.rng.random()
        self.levels_history = [(new_seed, map_type)]
        self.current_level_idx = 0
        self._generate_and_apply_map(new_seed, map_type, spawn_near_entrance=True)

    def go_to_next_level(self):
        """Avança para o próximo nível."""

        next_idx = self.current_level_idx + 1

        if next_idx < len(self.levels_history):
            # O mapa já foi visitado anteriormente.
            seed, map_type = self.levels_history[next_idx]

        else:
            # Novo mapa.
            seed = self.rng.random()
            map_type = self._get_next_map_type()

            self.levels_history.append(
                (seed, map_type)
            )

        self.current_level_idx = next_idx

        self._generate_and_apply_map(
            seed,
            map_type,
            spawn_near_entrance=True
        )

    def go_to_prev_level(self):
        """Recua para o nível anterior (bolinha branca)."""
        if self.current_level_idx <= 0:
            return  # Não há mapa anterior

        prev_idx = self.current_level_idx - 1
        seed, map_type = self.levels_history[prev_idx]
        self.current_level_idx = prev_idx
        self._generate_and_apply_map(seed, map_type, spawn_near_entrance=False)

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
            candidate_rect, self.walls
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

        # Jogador saiu da EXIT → reativa
        if not touching_exit:
            self.exit_triggered = False

        # Jogador entrou na EXIT novamente → avança
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

            # Jogador saiu da ENTRANCE → reativa
            if not touching_entrance:
                self.entrance_triggered = False

            # Jogador entrou na ENTRANCE novamente → recua
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
            )


if __name__ == "__main__":
    game = Game()
    game.run()
