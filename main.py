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
        pygame.display.set_caption('Mapas com Geração Procedural - Roguelike')
        self.clock = pygame.time.Clock()

        self.renderer = GameRenderer(self.screen)
        self.collision_manager = CollisionManager()
        self.player = Player()

        self.seed = random.random()
        self.rng = random.Random(self.seed)
        self.map_type = 0

        self.floors = []
        self.walls = []
        self.exit_pos = (0.0, 0.0)

        self._load_initial_map()

    def _load_initial_map(self):
        initial_map = MapService.create_initial_intro_map(self.seed)
        self._apply_map(initial_map)

    def _apply_map(self, mapa):
        self.floors, self.walls, player_pos, self.exit_pos = MapService.load_geometry(mapa, TILE_SIZE)
        self.player.set_position(player_pos[0], player_pos[1])

    def change_map(self, map_type: int):
        self.map_type = map_type
        mapa = MapService.generate_map(self.map_type, self.seed)
        self._apply_map(mapa)

    def next_level(self):
        self.seed = self.rng.random()
        mapa = MapService.generate_map(self.map_type, self.seed)
        self._apply_map(mapa)

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()

    def handle_shortcuts(self, keys):
        key_map_types = {
            pygame.K_r: 0,
            pygame.K_c: 1,
            pygame.K_b: 2,
            pygame.K_m: 3,
            pygame.K_f: 4,
            pygame.K_g: 5,
            pygame.K_h: 6,
        }

        for key, m_type in key_map_types.items():
            if keys[key]:
                self.change_map(m_type)
                break

    def update_player(self, keys):
        target_x, target_y = self.player.calculate_desired_position(keys)
        candidate_rect = self.player.get_rect(target_x, target_y)

        # Checa colisão com paredes antes de mover
        if not self.collision_manager.check_wall_collision(candidate_rect, self.walls):
            self.player.set_position(target_x, target_y)

        # Checa colisão com a saída
        exit_size = self.player.radius * 2
        exit_rect = pygame.Rect(
            self.exit_pos[0] - self.player.radius,
            self.exit_pos[1] - self.player.radius,
            exit_size,
            exit_size,
        )
        current_player_rect = self.player.get_rect()
        if self.collision_manager.check_trigger_collision(current_player_rect, exit_rect):
            self.next_level()

    def run(self):
        while True:
            self.clock.tick(FPS)
            self.handle_events()

            keys = pygame.key.get_pressed()
            self.handle_shortcuts(keys)
            self.update_player(keys)

            self.renderer.render_frame(self.floors, self.walls, self.player, self.exit_pos)

if __name__ == "__main__":
    game = Game()
    game.run()
