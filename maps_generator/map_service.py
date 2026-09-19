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
    def generate_map(map_type, seed, width=None, height=None):
        """Gera um mapa puro de um dos quatro algoritmos do projeto."""
        if width is None:
            width = WIDTH // TILE_SIZE
        if height is None:
            height = HEIGHT // TILE_SIZE

        if map_type == 0:
            mapa = RandomWalk(
                width=width,
                height=height,
                iterations=width * height * 4 // 5,
                seed=seed
            )
            mapa.generate()
            return mapa

        if map_type == 1:
            mapa = CellularAutomata(
                width=width,
                height=height,
                iterations=4,
                density=0.45,
                seed=seed
            )
            mapa.generate()
            return mapa

        if map_type == 2:
            mapa = Bsp(
                width=width,
                height=height,
                seed=seed,
                min_leaf_size=MIN_LEAF_SIZE
            )
            mapa.generate()
            return mapa

        if map_type == 3:
            mapa = HybridGenerator(
                width=width,
                height=height,
                seed=seed,
                min_leaf_size=MIN_LEAF_SIZE,
                density=0.7,
                iterations=3
            )
            mapa.generate()
            return mapa

        raise ValueError(f"Tipo de mapa inválido: {map_type}")

    @staticmethod
    def generate_intermediate_map(
        algorithm_a,
        algorithm_b,
        seed_a,
        seed_b,
        layout,
        reverse
    ):
        """
        Gera um mapa intermediário formado por dois submapas.

        layout:
            horizontal -> A | B
            vertical   -> A / B

        reverse:
            False -> A vem primeiro
            True  -> B vem primeiro
        """
        width = WIDTH // TILE_SIZE
        height = HEIGHT // TILE_SIZE

        if layout not in ("horizontal", "vertical"):
            raise ValueError(f"Layout inválido: {layout}")

        # Divide o tamanho preservando a célula restante quando a
        # dimensão é ímpar (25 -> 12 + 13).
        if layout == "horizontal":
            width_a = width // 2
            width_b = width - width_a
            height_a = height_b = height
        else:
            width_a = width_b = width
            height_a = height // 2
            height_b = height - height_a

        mapa_a = MapService.generate_map(
            algorithm_a,
            seed_a,
            width=width_a,
            height=height_a
        )

        mapa_b = MapService.generate_map(
            algorithm_b,
            seed_b,
            width=width_b,
            height=height_b
        )

        mapa = MapGenerator(
            width=width,
            height=height,
            seed=seed_a
        )

        maps = [mapa_a, mapa_b]

        if reverse:
            maps.reverse()

        mapa.join_maps(maps)

        # As posições são obtidas depois do join_maps(), pois o método
        # define world_x/world_y de cada submapa no mapa composto.
        region_a = (
            mapa_a.world_x,
            mapa_a.world_y,
            mapa_a.width,
            mapa_a.height
        )

        region_b = (
            mapa_b.world_x,
            mapa_b.world_y,
            mapa_b.width,
            mapa_b.height
        )

        spawn_info = {
            "type": "intermediate",
            "region_a": region_a,
            "region_b": region_b,
            "layout": layout,
        }

        return mapa, spawn_info

    @staticmethod
    def _tile_center(point, tile_size):
        x, y = point
        return (
            x * tile_size + tile_size / 2,
            y * tile_size + tile_size / 2
        )

    @staticmethod
    def _choose_pure_spawn_points(floors, width, height, seed):
        """
        Escolhe entrance e exit em regiões periféricas do mapa.

        Em vez de usar o centro como referência para o spawn, os pontos
        são classificados pela distância ao centro geométrico. A entrance
        é sorteada entre os pontos mais periféricos e o exit é escolhido
        como o ponto periférico mais distante dela.
        """
        if not floors:
            return (0, 0), (0, 0)

        rng = random.Random(seed)
        floor_list = list(floors)

        center_x = (width - 1) / 2
        center_y = (height - 1) / 2

        # Ordena os tiles de chão do mais periférico para o mais central.
        peripheral_floors = sorted(
            floor_list,
            key=lambda p: (
                (p[0] - center_x) ** 2
                + (p[1] - center_y) ** 2
            ),
            reverse=True
        )

        # Usa os 35% mais periféricos como região válida para entrance
        # e exit. Assim ambos ficam afastados do centro mesmo quando um
        # algoritmo não produz chão diretamente nas bordas do mapa.
        candidate_count = max(
            1,
            int(len(peripheral_floors) * 0.35)
        )

        candidates = peripheral_floors[:candidate_count]

        entrance = rng.choice(candidates)

        exit_point = max(
            candidates,
            key=lambda p: (
                (p[0] - entrance[0]) ** 2
                + (p[1] - entrance[1]) ** 2
            )
        )

        # Em mapas muito pequenos, ainda pode acontecer de existir apenas
        # um candidato. Nesse caso, procura o ponto mais distante em todo
        # o mapa para evitar que entrance e exit coincidam.
        if exit_point == entrance and len(floor_list) > 1:
            exit_point = max(
                floor_list,
                key=lambda p: (
                    (p[0] - entrance[0]) ** 2
                    + (p[1] - entrance[1]) ** 2
                )
            )

        return entrance, exit_point

    @staticmethod
    def _choose_intermediate_spawn_points(
        floors,
        region_a,
        region_b,
        layout,
        seed
    ):
        """
        Escolhe os pontos de transição de um mapa intermediário.

        A entrance pertence obrigatoriamente ao submapa A e o exit ao
        submapa B. Os pontos são escolhidos próximos às bordas externas
        dos respectivos submapas, fazendo o jogador atravessar a composição.
        """
        if not floors:
            return (0, 0), (0, 0)

        rng = random.Random(seed)

        ax, ay, aw, ah = region_a
        bx, by, bw, bh = region_b

        def in_region(point, region):
            x, y = point
            rx, ry, rw, rh = region
            return (
                rx <= x < rx + rw
                and ry <= y < ry + rh
            )

        floors_a = [p for p in floors if in_region(p, region_a)]
        floors_b = [p for p in floors if in_region(p, region_b)]

        if not floors_a or not floors_b:
            raise ValueError(
                "Não foi possível encontrar chão nos submapas do mapa intermediário"
            )

        # A entrance deve ficar no lado externo de A e o exit no lado
        # externo de B. Assim, o jogador percorre A -> B em vez de
        # encontrar os dois pontos próximos à divisão central.
        if layout == "horizontal":
            if ax < bx:
                # A | B
                entrance_distance = lambda p: p[0] - ax
                exit_distance = lambda p: (bx + bw - 1) - p[0]
            else:
                # B | A
                entrance_distance = lambda p: (ax + aw - 1) - p[0]
                exit_distance = lambda p: p[0] - bx
        else:
            if ay < by:
                # A / B
                entrance_distance = lambda p: p[1] - ay
                exit_distance = lambda p: (by + bh - 1) - p[1]
            else:
                # B / A
                entrance_distance = lambda p: (ay + ah - 1) - p[1]
                exit_distance = lambda p: p[1] - by

        # Seleciona os pontos mais próximos das bordas externas.
        # Em caso de empate, a posição transversal é usada como critério
        # aleatório para não deixar os spawns sempre no mesmo lugar.
        min_a = min(entrance_distance(p) for p in floors_a)
        min_b = min(exit_distance(p) for p in floors_b)

        entrance_candidates = [
            p for p in floors_a
            if entrance_distance(p) <= min_a + 2
        ]
        exit_candidates = [
            p for p in floors_b
            if exit_distance(p) <= min_b + 2
        ]

        entrance = rng.choice(entrance_candidates)
        exit_point = rng.choice(exit_candidates)

        return entrance, exit_point

    @staticmethod
    def load_geometry(
        mapa: MapGenerator,
        tile_size: int,
        seed: float,
        spawn_info=None
    ) -> Tuple[
        List[pygame.Rect],
        List[pygame.Rect],
        Tuple[float, float],
        Tuple[float, float]
    ]:
        walls = []
        floors = []

        map_floors = mapa.get_floors()
        map_walls = mapa.get_walls()

        for x, y in map_floors:
            px = x * tile_size
            py = y * tile_size
            floors.append(
                pygame.Rect(px, py, tile_size, tile_size)
            )

        for x, y in map_walls:
            walls.append(
                pygame.Rect(
                    x * tile_size,
                    y * tile_size,
                    tile_size,
                    tile_size
                )
            )

        if spawn_info and spawn_info["type"] == "intermediate":
            entrance, exit_point = MapService._choose_intermediate_spawn_points(
                map_floors,
                spawn_info["region_a"],
                spawn_info["region_b"],
                spawn_info["layout"],
                seed
            )
        else:
            entrance, exit_point = MapService._choose_pure_spawn_points(
                map_floors,
                mapa.width,
                mapa.height,
                seed
            )

        return (
            floors,
            walls,
            MapService._tile_center(entrance, tile_size),
            MapService._tile_center(exit_point, tile_size)
        )
