import random

from maps_generator.BSP import BSP
from maps_generator.CellularAutomata import CellularAutomata
from maps_generator.RandomWalk import RandomWalk


class MixedGenerator:

    def __init__(
        self,
        width,
        height,
        seed,
        min_leaf_size=10,
        min_room_size=4,
        generators = None
    ):

        self.width = width
        self.height = height

        self.seed = seed

        self.min_leaf_size = min_leaf_size
        self.min_room_size = min_room_size

        self.rng = random.Random(seed)

        self.grid = [
            ['#' for _ in range(width)]
            for _ in range(height)
        ]

        self.corridors_grid = [
            ['#' for _ in range(width)]
            for _ in range(height)
        ]

        # BSP será usado como estrutura
        self.bsp = BSP(
            width=width,
            height=height,
            seed=seed,
            min_leaf_size=min_leaf_size,
            min_room_size=min_room_size
        )

        if generators is None:

            self.generators = [
                "BSP_ROOM",
                "CELLULAR",
                "RANDOM_WALK",
                "MIXED_CA_RW"
            ]

        else:
            self.generators = generators

    # ============================================================
    # COPY LOCAL GRID TO GLOBAL GRID
    # ============================================================

    def copy_generator_to_leaf(self, generator, leaf):

        for x, y in generator.floor_tiles:

            global_x = x + leaf.x
            global_y = y + leaf.y

            # segurança
            if (
                0 <= global_x < self.width and
                0 <= global_y < self.height
            ):
                self.grid[global_y][global_x] = '.'

    # ============================================================
    # ASSIGN GENERATOR TO LEAF
    # ============================================================

    def generate_leaf_content(self, leaf):

        generator_type = self.rng.choice(self.generators)

        # --------------------------------------------------------
        # BSP ROOM
        # --------------------------------------------------------

        if generator_type == "BSP_ROOM":

            temp_bsp = BSP(
                width=leaf.width,
                height=leaf.height,
                seed=self.rng.random(),
                min_leaf_size=leaf.width,
                min_room_size=max(
                    3,
                    self.min_room_size
                )
            )

            temp_bsp.generate_bsp_room(
                type(
                    "TempLeaf",
                    (),
                    {
                        "x": 0,
                        "y": 0,
                        "width": leaf.width,
                        "height": leaf.height,
                        "room": None,
                        "floor_tiles": [],
                        "connection_point": None
                    }
                )()
            )

            # copia floors
            for y in range(leaf.height):

                for x in range(leaf.width):

                    if temp_bsp.grid[y][x] == '.':
                        self.grid[y + leaf.y][x + leaf.x] = '.'

            # pega ponto central
            floors = []

            for y in range(leaf.height):
                for x in range(leaf.width):

                    if temp_bsp.grid[y][x] == '.':
                        floors.append((x, y))

            if floors:

                px, py = self.rng.choice(floors)

                leaf.connection_point = (
                    px + leaf.x,
                    py + leaf.y
                )

        # --------------------------------------------------------
        # CELLULAR AUTOMATA
        # --------------------------------------------------------

        elif generator_type == "CELLULAR":

            gen = CellularAutomata(
                width=leaf.width,
                height=leaf.height,
                iterations=6,
                density=0.5,
                seed=self.rng.random()
            )

            gen.generate()

            self.copy_generator_to_leaf(gen, leaf)

            if gen.connection_point:

                px, py = gen.connection_point

                leaf.connection_point = (
                    px + leaf.x,
                    py + leaf.y
                )

        # --------------------------------------------------------
        # RANDOM WALK
        # --------------------------------------------------------

        elif generator_type == "RANDOM_WALK":

            gen = RandomWalk(
                width=leaf.width,
                height=leaf.height,
                iterations=(
                    leaf.width *
                    leaf.height
                ) * 2 // 3,
                seed=self.rng.random()
            )

            gen.generate()

            self.copy_generator_to_leaf(gen, leaf)

            if gen.connection_point:

                px, py = gen.connection_point

                leaf.connection_point = (
                    px + leaf.x,
                    py + leaf.y
                )

        # --------------------------------------------------------
        # RANDOM WALK + CELLULAR
        # --------------------------------------------------------

        elif generator_type == "MIXED_CA_RW":

            rw = RandomWalk(
                width=leaf.width,
                height=leaf.height,
                iterations=(
                    leaf.width *
                    leaf.height
                ) * 3 // 4,
                seed=self.rng.random()
            )

            rw.generate()

            ca = CellularAutomata(
                width=leaf.width,
                height=leaf.height,
                iterations=3,
                density=0.45,
                seed=self.rng.random()
            )

            # usa resultado do RW
            ca.grid = [row[:] for row in rw.grid]

            ca.make_iterations()

            ca.find_floor_tiles()

            ca.choose_connection_point()

            self.copy_generator_to_leaf(ca, leaf)

            if ca.connection_point:

                px, py = ca.connection_point

                leaf.connection_point = (
                    px + leaf.x,
                    py + leaf.y
                )

    # ============================================================
    # GENERATE ALL LEAF CONTENTS
    # ============================================================

    def generate_regions(self):

        for leaf in self.bsp.leaves:

            self.generate_leaf_content(leaf)

    # ============================================================
    # CORRIDORS
    # ============================================================

    def carve_h(self, x1, x2, y):

        for x in range(
            min(x1, x2),
            max(x1, x2) + 1
        ):

            self.grid[y][x] = '.'
            self.corridors_grid[y][x]= '.'

    def carve_v(self, y1, y2, x):

        for y in range(
            min(y1, y2),
            max(y1, y2) + 1
        ):

            self.grid[y][x] = '.'
            self.corridors_grid[y][x]= '.'

    def connect_points(self, p1, p2):

        x1, y1 = p1
        x2, y2 = p2

        if self.rng.random() < 0.5:

            self.carve_h(x1, x2, y1)

            self.carve_v(y1, y2, x2)

        else:

            self.carve_v(y1, y2, x1)

            self.carve_h(x1, x2, y2)

    # ============================================================
    # TREE CONNECTION
    # ============================================================

    def get_connection_point(self, leaf):

        # leaf válida
        if leaf.connection_point is not None:
            return leaf.connection_point

        points = []

        # filho esquerdo
        if leaf.left_child:

            point = self.get_connection_point(
                leaf.left_child
            )

            if point is not None:
                points.append(point)

        # filho direito
        if leaf.right_child:

            point = self.get_connection_point(
                leaf.right_child
            )

            if point is not None:
                points.append(point)

        # nenhuma região válida
        if not points:
            return None

        return self.rng.choice(points)

    def connect_tree(self, leaf):

        if (
            leaf.left_child is None or
            leaf.right_child is None
        ):
            return

        left_point = self.get_connection_point(
            leaf.left_child
        )

        right_point = self.get_connection_point(
            leaf.right_child
        )

        # só conecta se ambos existirem
        if (
            left_point is not None and
            right_point is not None
        ):

            self.connect_points(
                left_point,
                right_point
            )

        self.connect_tree(leaf.left_child)

        self.connect_tree(leaf.right_child)


    # ============================================================
    # CORRIDORS DETAILS
    # ============================================================

    def corridors_details(self):
        ra_map = RandomWalk(
            width=self.width,
            height=self.height,
            iterations=3,
            seed=self.seed
        )

        ra_map.grid = self.corridors_grid
        ra_map.multi_walk()
        
        for x,y in ra_map.floor_tiles:
            self.grid[y][x] = '.'
            self.corridors_grid[y][x] = '.'

        
    # ============================================================
    # PIPELINE
    # ============================================================

    def generate(self):

        # 1. divide espaço
        self.bsp.generate_bsp()

        # 2. gera conteúdo procedural
        self.generate_regions()

        # 3. conecta regiões
        self.connect_tree(self.bsp.root)

        self.corridors_details()


        

    # ============================================================
    # DEBUG
    # ============================================================

    def print_map(self):

        for row in self.grid:
            print("".join(row))