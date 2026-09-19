import pygame
import random
from typing import List, Tuple
from config import WIDTH, HEIGHT, TILE_SIZE, MIN_LEAF_SIZE
from maps_generator.mapGenerator import MapGenerator
from maps_generator.bsp import Bsp
from maps_generator.randomWalk import RandomWalk
from maps_generator.cellularAutomata import CellularAutomata
from maps_generator.hybridGenerator import HybridGenerator

class MapService:
    @staticmethod
    def create_initial_intro_map(seed: float) -> MapGenerator:
        grid_w = WIDTH // TILE_SIZE
        grid_h = HEIGHT // TILE_SIZE
        initial_map = MapGenerator(width=grid_w, height=grid_h, seed=seed)
        grid = [['.' for _ in range(grid_w)] for _ in range(grid_h)]

        letters = {
            0: [0, 4, 6, 7, 8, 9, 10, 12, 13, 14, 15, 16],
            1: [0, 1, 3, 4, 6, 10, 12, 16],
            2: [0, 2, 4, 6, 7, 8, 9, 10, 12, 13, 14, 15, 16],
            3: [0, 4, 6, 10, 12],
            4: [0, 4, 6, 10, 12],
            6: [0, 1, 2, 3, 4, 6, 7, 8, 9, 10, 12, 16],
            7: [0, 6, 12, 13, 16],
            8: [0, 3, 4, 6, 7, 8, 9, 12, 14, 16],
            9: [0, 4, 6, 12, 15, 16],
            10: [0, 1, 2, 3, 4, 6, 7, 8, 9, 10, 12, 16],
        }

        for key, vals in letters.items():
            y = key + 5
            for valor in vals:
                x = valor + 12
                if 0 <= y < grid_h and 0 <= x < grid_w:
                    grid[y][x] = '#'

        initial_map.grid = grid
        return initial_map

    @staticmethod
    def generate_map(map_type: int, seed: float) -> MapGenerator:
        width = WIDTH // TILE_SIZE
        height = HEIGHT // TILE_SIZE

        if map_type == 0:
            mapa = RandomWalk(width=width, height=height, iterations=width * height * 4 // 5, seed=seed)
            mapa.generate()
            return mapa
        elif map_type == 1:
            mapa = CellularAutomata(width=width, height=height, iterations=4, density=0.45, seed=seed)
            mapa.generate()
            return mapa
        elif map_type == 2:
            mapa = Bsp(width=width, height=height, seed=seed, min_leaf_size=MIN_LEAF_SIZE)
            mapa.generate()
            return mapa
        elif map_type == 3:
            mapa = HybridGenerator(width=width, height=height, seed=seed, min_leaf_size=MIN_LEAF_SIZE, density=0.7, iterations=3)
            mapa.generate()
            return mapa
        elif map_type == 4:
            mapa1 = Bsp(width=width // 2, height=height, seed=seed, min_leaf_size=MIN_LEAF_SIZE)
            mapa1.generate()
            mapa2 = HybridGenerator(width=width // 2, height=height, seed=seed, min_leaf_size=MIN_LEAF_SIZE, density=0.7, iterations=3)
            mapa2.generate()
            mapa = MapGenerator(width=width, height=height, seed=seed)
            mapa.join_maps([mapa1, mapa2])
            return mapa
        elif map_type == 5:
            mapa1 = HybridGenerator(width=width // 2, height=height, seed=seed, min_leaf_size=MIN_LEAF_SIZE, density=0.7, iterations=3)
            mapa1.generate()
            mapa2 = CellularAutomata(width=width // 2, height=height, seed=seed, density=0.5, iterations=4)
            mapa2.generate()
            mapa = MapGenerator(width=width, height=height, seed=seed)
            mapa.join_maps([mapa1, mapa2])
            return mapa
        elif map_type == 6:
            mapa1 = CellularAutomata(width=width // 2, height=height, seed=seed, density=0.5, iterations=4)
            mapa1.generate()
            mapa2 = RandomWalk(width=width // 2, height=height, seed=seed, iterations=width * height * 2 // 5)
            mapa2.generate()
            mapa = MapGenerator(width=width, height=height, seed=seed)
            mapa.join_maps([mapa1, mapa2])
            return mapa
        else:
            return MapService.create_initial_intro_map(seed)

    @staticmethod
    def load_geometry(mapa: MapGenerator, tile_size: int, seed: float) -> Tuple[List[pygame.Rect], List[pygame.Rect], Tuple[float, float], Tuple[float, float]]:
        walls = []
        floors = []

        map_floors = mapa.get_floors()
        map_walls = mapa.get_walls()

        for x, y in map_floors:
            px = x * tile_size
            py = y * tile_size
            floors.append(pygame.Rect(px, py, tile_size, tile_size))

        for x, y in map_walls:
            walls.append(pygame.Rect(x * tile_size, y * tile_size, tile_size, tile_size))

        rng = random.Random(seed)
        entrance_x = entrance_y = exit_x = exit_y = 0.0

        if map_floors:
            floor_choices = list(map_floors)
            rng.shuffle(floor_choices)
            entrance = floor_choices[0]

            exit_point = entrance
            max_dist = -1
            for f in floor_choices:
                dist = (f[0] - entrance[0])**2 + (f[1] - entrance[1])**2
                if dist > max_dist:
                    max_dist = dist
                    exit_point = f

            entrance_x = entrance[0] * tile_size + tile_size / 2
            entrance_y = entrance[1] * tile_size + tile_size / 2
            exit_x = exit_point[0] * tile_size + tile_size / 2
            exit_y = exit_point[1] * tile_size + tile_size / 2

        return floors, walls, (entrance_x, entrance_y), (exit_x, exit_y)
