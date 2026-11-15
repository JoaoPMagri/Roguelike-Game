import pygame
import random
from typing import List, Tuple

from config import (
    WIDTH,
    HEIGHT,
    TILE_SIZE,
    MAP_WIDTH,
    MAP_HEIGHT,
    MIN_LEAF_SIZE,
    MIN_DOOR_DISTANCE_TILES,
    OBSTACLE_SPAWN_CHANCE,
)
from maps_generator.mapGenerator import MapGenerator
from maps_generator.bsp import Bsp
from maps_generator.randomWalk import RandomWalk
from maps_generator.cellularAutomata import CellularAutomata
from maps_generator.hybridGenerator import HybridGenerator


class MapService:

    OPPOSITE_SIDES = {
        "top": "bottom",
        "bottom": "top",
        "left": "right",
        "right": "left"
    }

    @staticmethod
    def generate_map(map_type, seed, width=None, height=None):
        """Gera um mapa puro de um dos quatro algoritmos do projeto."""
        if width is None:
            width = MAP_WIDTH
        if height is None:
            height = MAP_HEIGHT

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
        width = MAP_WIDTH
        height = MAP_HEIGHT

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

    # @staticmethod
    # def _choose_pure_spawn_points(floors, width, height, seed):
    #     """
    #     Escolhe entrance e exit em regiões periféricas do mapa.

    #     Em vez de usar o centro como referência para o spawn, os pontos
    #     são classificados pela distância ao centro geométrico. A entrance
    #     é sorteada entre os pontos mais periféricos e o exit é escolhido
    #     como o ponto periférico mais distante dela.
    #     """
    #     if not floors:
    #         return (0, 0), (0, 0)

    #     rng = random.Random(seed)
    #     floor_list = list(floors)

    #     center_x = (width - 1) / 2
    #     center_y = (height - 1) / 2

    #     # Ordena os tiles de chão do mais periférico para o mais central.
    #     peripheral_floors = sorted(
    #         floor_list,
    #         key=lambda p: (
    #             (p[0] - center_x) ** 2
    #             + (p[1] - center_y) ** 2
    #         ),
    #         reverse=True
    #     )

    #     # Usa os 35% mais periféricos como região válida para entrance
    #     # e exit. Assim ambos ficam afastados do centro mesmo quando um
    #     # algoritmo não produz chão diretamente nas bordas do mapa.
    #     candidate_count = max(
    #         1,
    #         int(len(peripheral_floors) * 0.35)
    #     )

    #     candidates = peripheral_floors[:candidate_count]

    #     entrance = rng.choice(candidates)

    #     exit_point = max(
    #         candidates,
    #         key=lambda p: (
    #             (p[0] - entrance[0]) ** 2
    #             + (p[1] - entrance[1]) ** 2
    #         )
    #     )

    #     # Em mapas muito pequenos, ainda pode acontecer de existir apenas
    #     # um candidato. Nesse caso, procura o ponto mais distante em todo
    #     # o mapa para evitar que entrance e exit coincidam.
    #     if exit_point == entrance and len(floor_list) > 1:
    #         exit_point = max(
    #             floor_list,
    #             key=lambda p: (
    #                 (p[0] - entrance[0]) ** 2
    #                 + (p[1] - entrance[1]) ** 2
    #             )
    #         )

    #     return entrance, exit_point

    # @staticmethod
    # def _choose_intermediate_spawn_points(
    #     floors,
    #     region_a,
    #     region_b,
    #     layout,
    #     seed
    # ):
    #     """
    #     Escolhe os pontos de transição de um mapa intermediário.

    #     A entrance pertence obrigatoriamente ao submapa A e o exit ao
    #     submapa B. Os pontos são escolhidos próximos às bordas externas
    #     dos respectivos submapas, fazendo o jogador atravessar a composição.
    #     """
    #     if not floors:
    #         return (0, 0), (0, 0)

    #     rng = random.Random(seed)

    #     ax, ay, aw, ah = region_a
    #     bx, by, bw, bh = region_b

    #     def in_region(point, region):
    #         x, y = point
    #         rx, ry, rw, rh = region
    #         return (
    #             rx <= x < rx + rw
    #             and ry <= y < ry + rh
    #         )

    #     floors_a = [p for p in floors if in_region(p, region_a)]
    #     floors_b = [p for p in floors if in_region(p, region_b)]

    #     if not floors_a or not floors_b:
    #         raise ValueError(
    #             "Não foi possível encontrar chão nos submapas do mapa intermediário"
    #         )

    #     # A entrance deve ficar no lado externo de A e o exit no lado
    #     # externo de B. Assim, o jogador percorre A -> B em vez de
    #     # encontrar os dois pontos próximos à divisão central.
    #     if layout == "horizontal":
    #         if ax < bx:
    #             # A | B
    #             entrance_distance = lambda p: p[0] - ax
    #             exit_distance = lambda p: (bx + bw - 1) - p[0]
    #         else:
    #             # B | A
    #             entrance_distance = lambda p: (ax + aw - 1) - p[0]
    #             exit_distance = lambda p: p[0] - bx
    #     else:
    #         if ay < by:
    #             # A / B
    #             entrance_distance = lambda p: p[1] - ay
    #             exit_distance = lambda p: (by + bh - 1) - p[1]
    #         else:
    #             # B / A
    #             entrance_distance = lambda p: (ay + ah - 1) - p[1]
    #             exit_distance = lambda p: p[1] - by

    #     # Seleciona os pontos mais próximos das bordas externas.
    #     # Em caso de empate, a posição transversal é usada como critério
    #     # aleatório para não deixar os spawns sempre no mesmo lugar.
    #     min_a = min(entrance_distance(p) for p in floors_a)
    #     min_b = min(exit_distance(p) for p in floors_b)

    #     entrance_candidates = [
    #         p for p in floors_a
    #         if entrance_distance(p) <= min_a + 2
    #     ]
    #     exit_candidates = [
    #         p for p in floors_b
    #         if exit_distance(p) <= min_b + 2
    #     ]

    #     entrance = rng.choice(entrance_candidates)
    #     exit_point = rng.choice(exit_candidates)

    #     return entrance, exit_point

    @staticmethod
    def find_door(walls, floors, side, map_width, map_height):
        floor_positions = {
            (rect.x, rect.y)
            for rect in floors
        }

        candidates = []

        for wall in walls:
            x = wall.x
            y = wall.y

            if side == "top":
                if y != 0:
                    continue

                floor_pos = (x, y + TILE_SIZE)

            elif side == "bottom":
                if y != map_height - TILE_SIZE:
                    continue

                floor_pos = (x, y - TILE_SIZE)

            elif side == "left":
                if x != 0:
                    continue

                floor_pos = (x + TILE_SIZE, y)

            elif side == "right":
                if x != map_width - TILE_SIZE:
                    continue

                floor_pos = (x - TILE_SIZE, y)

            else:
                continue

            if floor_pos in floor_positions:
                candidates.append({
                    "tile": (x, y),
                    "floor": floor_pos,
                    "side": side
                })

        if not candidates:
            return None

        return random.choice(candidates)

    @staticmethod
    def _find_door_candidates(floors, walls, side, map_width, map_height):
        """Retorna apenas paredes que realmente existem na geometria gerada.

        A porta nunca é inventada em uma coordenada aleatória. Para cada
        parede candidata também exigimos que exista chão imediatamente
        para o lado interno, pois esse é o ponto onde o jogador ficará.
        """
        floor_positions = {(rect.x, rect.y) for rect in floors}
        wall_positions = {(rect.x, rect.y) for rect in walls}

        max_x = map_width - TILE_SIZE
        max_y = map_height - TILE_SIZE
        candidates = []

        for wall_x, wall_y in wall_positions:
            if side == "top":
                if wall_y == 0:
                    floor_pos = (wall_x, wall_y + TILE_SIZE)
                    if floor_pos in floor_positions:
                        candidates.append(((wall_x, wall_y), floor_pos))

            elif side == "bottom":
                if wall_y == max_y:
                    floor_pos = (wall_x, wall_y - TILE_SIZE)
                    if floor_pos in floor_positions:
                        candidates.append(((wall_x, wall_y), floor_pos))

            elif side == "left":
                if wall_x == 0:
                    floor_pos = (wall_x + TILE_SIZE, wall_y)
                    if floor_pos in floor_positions:
                        candidates.append(((wall_x, wall_y), floor_pos))

            elif side == "right":
                if wall_x == max_x:
                    floor_pos = (wall_x - TILE_SIZE, wall_y)
                    if floor_pos in floor_positions:
                        candidates.append(((wall_x, wall_y), floor_pos))

        return candidates

    @staticmethod
    def _find_nearest_door_candidates(floors, walls, side, map_width, map_height):
        """Fallback: escolhe paredes existentes mais próximas do lado pedido.

        Esse fallback é usado somente quando o algoritmo não possui uma
        parede válida exatamente na borda solicitada. Ainda assim, a porta
        continua sendo uma parede REAL produzida pelo gerador; nenhuma
        parede ou chão é criado artificialmente.
        """
        floor_positions = {(rect.x, rect.y) for rect in floors}
        wall_positions = {(rect.x, rect.y) for rect in walls}

        max_x = map_width - TILE_SIZE
        max_y = map_height - TILE_SIZE
        candidates = []

        for wall_x, wall_y in wall_positions:
            if side == "top":
                floor_pos = (wall_x, wall_y + TILE_SIZE)
                if floor_pos not in floor_positions or wall_y >= max_y:
                    continue
                distance = wall_y

            elif side == "bottom":
                floor_pos = (wall_x, wall_y - TILE_SIZE)
                if floor_pos not in floor_positions or wall_y <= 0:
                    continue
                distance = max_y - wall_y

            elif side == "left":
                floor_pos = (wall_x + TILE_SIZE, wall_y)
                if floor_pos not in floor_positions or wall_x >= max_x:
                    continue
                distance = wall_x

            elif side == "right":
                floor_pos = (wall_x - TILE_SIZE, wall_y)
                if floor_pos not in floor_positions or wall_x <= 0:
                    continue
                distance = max_x - wall_x

            else:
                continue

            candidates.append((distance, (wall_x, wall_y), floor_pos))

        if not candidates:
            return []

        minimum_distance = min(item[0] for item in candidates)
        return [
            (door_pos, floor_pos)
            for distance, door_pos, floor_pos in candidates
            if distance == minimum_distance
        ]

    @staticmethod
    def _ensure_door(floors, walls, side, map_width, map_height, rng):
        """Seleciona uma porta a partir das paredes do mapa gerado.

        A prioridade é:
        1. parede existente exatamente na borda solicitada;
        2. caso não exista, parede existente mais próxima daquela borda.

        Nunca são criados tiles de parede/chão para fabricar uma porta.
        """
        valid_sides = {"top", "bottom", "left", "right"}
        if side not in valid_sides:
            return None

        candidates = MapService._find_door_candidates(
            floors,
            walls,
            side,
            map_width,
            map_height
        )

        if not candidates:
            candidates = MapService._find_nearest_door_candidates(
                floors,
                walls,
                side,
                map_width,
                map_height
            )

        if not candidates:
            return None

        door_pos, floor_pos = rng.choice(candidates)

        return {
            "tile": door_pos,
            "floor": floor_pos,
            "side": side
        }

    @staticmethod
    def _select_door_pair(
        floors,
        walls,
        entrance_side,
        exit_side,
        map_width,
        map_height,
        rng
    ):
        """Seleciona entrada e saída evitando que fiquem muito próximas.

        As duas portas continuam sendo escolhidas somente entre paredes
        existentes na geometria gerada. Primeiro são considerados os
        candidatos que atendem exatamente às bordas pedidas; o fallback
        existente de cada lado só é usado quando necessário.

        A seleção procura pares cuja distância seja pelo menos
        ``MIN_DOOR_DISTANCE_TILES``. Se o mapa não permitir essa distância,
        escolhe o par mais distante possível em vez de fabricar geometria.
        """
        entrance_candidates = MapService._find_door_candidates(
            floors,
            walls,
            entrance_side,
            map_width,
            map_height
        )
        if not entrance_candidates:
            entrance_candidates = MapService._find_nearest_door_candidates(
                floors,
                walls,
                entrance_side,
                map_width,
                map_height
            )

        exit_candidates = MapService._find_door_candidates(
            floors,
            walls,
            exit_side,
            map_width,
            map_height
        )
        if not exit_candidates:
            exit_candidates = MapService._find_nearest_door_candidates(
                floors,
                walls,
                exit_side,
                map_width,
                map_height
            )

        if not entrance_candidates or not exit_candidates:
            return None, None

        min_distance_px = MIN_DOOR_DISTANCE_TILES * TILE_SIZE

        pairs = []
        for entrance in entrance_candidates:
            entrance_pos = entrance[0]

            for exit_door in exit_candidates:
                exit_pos = exit_door[0]

                if entrance_pos == exit_pos:
                    continue

                dx = entrance_pos[0] - exit_pos[0]
                dy = entrance_pos[1] - exit_pos[1]
                distance_squared = dx * dx + dy * dy

                pairs.append((distance_squared, entrance, exit_door))

        if not pairs:
            return None, None

        # Primeiro tenta satisfazer a distância mínima configurada.
        min_distance_squared = min_distance_px * min_distance_px
        valid_pairs = [
            pair
            for pair in pairs
            if pair[0] >= min_distance_squared
        ]

        if valid_pairs:
            _, entrance, exit_door = rng.choice(valid_pairs)
        else:
            # Mapas muito pequenos/estreitos podem não comportar a
            # distância desejada. Nesse caso, usa o par mais distante
            # possível, mantendo a geometria original intacta.
            max_distance = max(pair[0] for pair in pairs)
            farthest_pairs = [
                pair
                for pair in pairs
                if pair[0] == max_distance
            ]
            _, entrance, exit_door = rng.choice(farthest_pairs)

        entrance_pos, entrance_floor = entrance
        exit_pos, exit_floor = exit_door

        return (
            {
                "tile": entrance_pos,
                "floor": entrance_floor,
                "side": entrance_side
            },
            {
                "tile": exit_pos,
                "floor": exit_floor,
                "side": exit_side
            }
        )

    @staticmethod
    def find_spawn_position(floors, walls, side, map_width, map_height, rng):
        """Escolhe apenas a posição inicial do primeiro mapa.

        Não cria porta nem altera a geometria. Primeiro procura um chão
        imediatamente atrás de uma parede existente na borda indicada.
        Se o gerador não tiver essa configuração, usa o chão existente
        mais próximo da borda solicitada.
        """
        floor_positions = {(rect.x, rect.y) for rect in floors}
        wall_positions = {(rect.x, rect.y) for rect in walls}

        max_x = map_width - TILE_SIZE
        max_y = map_height - TILE_SIZE
        candidates = []

        for floor_x, floor_y in floor_positions:
            if side == "top":
                wall_pos = (floor_x, floor_y - TILE_SIZE)
                if wall_pos in wall_positions:
                    distance = floor_y
                else:
                    continue
            elif side == "bottom":
                wall_pos = (floor_x, floor_y + TILE_SIZE)
                if wall_pos in wall_positions:
                    distance = max_y - floor_y
                else:
                    continue
            elif side == "left":
                wall_pos = (floor_x - TILE_SIZE, floor_y)
                if wall_pos in wall_positions:
                    distance = floor_x
                else:
                    continue
            elif side == "right":
                wall_pos = (floor_x + TILE_SIZE, floor_y)
                if wall_pos in wall_positions:
                    distance = max_x - floor_x
                else:
                    continue
            else:
                continue

            candidates.append((distance, (floor_x, floor_y)))

        if not candidates:
            # Sem alterar o mapa, escolhe o chão existente mais próximo
            # da borda desejada.
            for floor_x, floor_y in floor_positions:
                if side == "top":
                    distance = floor_y
                elif side == "bottom":
                    distance = max_y - floor_y
                elif side == "left":
                    distance = floor_x
                else:
                    distance = max_x - floor_x
                candidates.append((distance, (floor_x, floor_y)))

        if not candidates:
            return None

        minimum_distance = min(distance for distance, _ in candidates)
        nearest = [pos for distance, pos in candidates if distance == minimum_distance]
        return rng.choice(nearest)

    @staticmethod
    def load_geometry(
        mapa: MapGenerator,
        tile_size: int,
        seed: float,
        spawn_info=None,
        entrance_side=None,
        exit_side=None,
        spawn_side=None
    ):
        walls = []
        floors = []

        map_floors = mapa.get_floors()
        map_walls = mapa.get_walls()

        for x, y in map_floors:
            floors.append(
                pygame.Rect(
                    x * tile_size,
                    y * tile_size,
                    tile_size,
                    tile_size
                )
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

        map_width = mapa.width * tile_size
        map_height = mapa.height * tile_size

        # A mesma seed produz as mesmas posições de portas ao recarregar
        # um nível do histórico.
        rng = random.Random(seed)

        entrance = None
        exit_door = None
        spawn_position = None

        if spawn_side is not None:
            spawn_position = MapService.find_spawn_position(
                floors,
                walls,
                spawn_side,
                map_width,
                map_height,
                rng
            )

        if exit_side is None:
            sides = ["top", "bottom", "left", "right"]

            if entrance_side is not None and entrance_side in sides:
                sides.remove(entrance_side)

            exit_side = rng.choice(sides)

        if entrance_side is not None:
            # Quando existem as duas portas, elas são escolhidas em conjunto.
            # Isso evita que a entrada e a saída caiam próximas, principalmente
            # quando estão em lados adjacentes do mapa.
            entrance, exit_door = MapService._select_door_pair(
                floors,
                walls,
                entrance_side,
                exit_side,
                map_width,
                map_height,
                rng
            )
        else:
            # Primeiro mapa: não há porta de entrada, somente a saída.
            exit_door = MapService._ensure_door(
                floors,
                walls,
                exit_side,
                map_width,
                map_height,
                rng
            )

        forbidden_positions = set()
        if spawn_position is not None:
            forbidden_positions.add(spawn_position)
        if entrance is not None:
            forbidden_positions.add(entrance["floor"])
        if exit_door is not None:
            forbidden_positions.add(exit_door["floor"])

        obstacles, obstacle_effects = MapService.generate_obstacles(
            floors=floors,
            tile_size=tile_size,
            rng=rng,
            forbidden_positions=forbidden_positions,
            spawn_chance=OBSTACLE_SPAWN_CHANCE,
        )

        return (
            floors,
            walls,
            obstacles,
            obstacle_effects,
            entrance,
            exit_door,
            spawn_position
        )

    @staticmethod
    def generate_obstacles(
        floors,
        tile_size: int,
        rng: random.Random,
        forbidden_positions: set,
        spawn_chance: float = 0.02,
    ) -> tuple[List[pygame.Rect], List[dict]]:
        """
        Gera obstáculos esparsos apenas em áreas bem abertas (anel 5x5 de chão),
        garantindo que o jogador consiga contornar o obstáculo e seus efeitos
        sem sofrer dano. Os efeitos ao redor têm tamanhos aleatórios.
        """
        floor_positions = {(rect.x, rect.y) for rect in floors}
        neighbors_offsets = [
            (-tile_size, -tile_size), (0, -tile_size), (tile_size, -tile_size),
            (-tile_size, 0),                           (tile_size, 0),
            (-tile_size, tile_size),  (0, tile_size),  (tile_size, tile_size),
        ]

        # Exige uma área aberta 5x5 (distância de 2 tiles em todas as direções)
        area_5x5_offsets = [
            (dx * tile_size, dy * tile_size)
            for dy in range(-2, 3)
            for dx in range(-2, 3)
            if not (dx == 0 and dy == 0)
        ]

        # Distância mínima entre obstáculos para evitar barreiras de efeitos
        spacing_offsets = [
            (dx * tile_size, dy * tile_size)
            for dy in range(-3, 4)
            for dx in range(-3, 4)
            if not (dx == 0 and dy == 0)
        ]

        open_candidates = []
        for fx, fy in sorted(floor_positions):
            if (fx, fy) in forbidden_positions:
                continue
            # Não coloca obstáculo nem efeito colado em pontos proibidos (portas/spawn)
            if any((fx + dx, fy + dy) in forbidden_positions for dx, dy in neighbors_offsets):
                continue
            if all((fx + dx, fy + dy) in floor_positions for dx, dy in area_5x5_offsets):
                open_candidates.append((fx, fy))

        obstacles = []
        placed_positions = set()

        for fx, fy in open_candidates:
            if any((fx + dx, fy + dy) in placed_positions for dx, dy in spacing_offsets):
                continue

            if rng.random() < spawn_chance:
                placed_positions.add((fx, fy))
                obstacles.append(pygame.Rect(fx, fy, tile_size, tile_size))

        # Garante ao menos 1 obstáculo mesmo em mapas mais fechados
        if not obstacles:
            fallback_pos = None
            if open_candidates:
                fallback_pos = rng.choice(open_candidates)
            else:
                area_3x3_candidates = [
                    (fx, fy)
                    for fx, fy in sorted(floor_positions)
                    if (fx, fy) not in forbidden_positions
                    and not any((fx + dx, fy + dy) in forbidden_positions for dx, dy in neighbors_offsets)
                    and all((fx + dx, fy + dy) in floor_positions for dx, dy in neighbors_offsets)
                ]
                if area_3x3_candidates:
                    fallback_pos = rng.choice(area_3x3_candidates)
                else:
                    any_floor = [
                        (fx, fy)
                        for fx, fy in sorted(floor_positions)
                        if (fx, fy) not in forbidden_positions
                    ]
                    if any_floor:
                        fallback_pos = rng.choice(any_floor)

            if fallback_pos is not None:
                placed_positions.add(fallback_pos)
                obstacles.append(
                    pygame.Rect(fallback_pos[0], fallback_pos[1], tile_size, tile_size)
                )

        obstacle_effects = []
        effect_positions = set()
        # O sprite de efeito é orientado com o obstáculo abaixo (0, -tile_size -> 0°).
        # pygame.transform.rotate gira no sentido anti-horário.
        effect_angles = {
            (0, -tile_size): 0,
            (-tile_size, -tile_size): 45,
            (-tile_size, 0): 90,
            (-tile_size, tile_size): 135,
            (0, tile_size): 180,
            (tile_size, tile_size): 225,
            (tile_size, 0): 270,
            (tile_size, -tile_size): 315,
        }
        for obs in obstacles:
            for dx, dy in neighbors_offsets:
                ex, ey = obs.x + dx, obs.y + dy
                pos = (ex, ey)
                if (
                    pos in floor_positions
                    and pos not in placed_positions
                    and pos not in effect_positions
                ):
                    effect_positions.add(pos)
                    scale = rng.uniform(0.55, 0.95)
                    size = max(16, int(tile_size * scale))
                    margin = tile_size - size
                    offset_x = rng.randint(0, margin) if margin > 0 else 0
                    offset_y = rng.randint(0, margin) if margin > 0 else 0
                    obstacle_effects.append({
                        "rect": pygame.Rect(ex + offset_x, ey + offset_y, size, size),
                        "obstacle_rect": obs,
                        "initial_frame": rng.choice([0, 1]),
                        "angle": effect_angles[(dx, dy)],
                    })

        return obstacles, obstacle_effects
