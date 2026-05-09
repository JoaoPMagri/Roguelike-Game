import random


class CellularAutomata:

    def __init__(
        self,
        width,
        height,
        iterations,
        seed,
        density=0.5
    ):

        self.width = width
        self.height = height

        self.iterations = iterations
        self.density = density

        self.rng = random.Random(seed)

        self.grid = [
            ['#' for _ in range(width)]
            for _ in range(height)
        ]

        self.grid_textured = [
            ['#' for _ in range(width)]
            for _ in range(height)
        ]

        # padronização
        self.floor_tiles = []
        self.connection_point = None

    # ============================================================
    # RANDOM INITIALIZATION
    # ============================================================

    def generate_random(self):

        for y in range(self.height):

            for x in range(self.width):

                if self.rng.random() < self.density:
                    self.grid[y][x] = '.'

    # ============================================================
    # WALL COUNT
    # ============================================================

    def count_walls_around(self, x, y):

        walls = 0

        for dy in [-1, 0, 1]:

            for dx in [-1, 0, 1]:

                if dx == 0 and dy == 0:
                    continue

                nx = x + dx
                ny = y + dy

                # fora do mapa = parede
                if (
                    nx < 0 or
                    ny < 0 or
                    nx >= self.width or
                    ny >= self.height
                ):
                    walls += 1

                elif self.grid[ny][nx] == '#':
                    walls += 1

        return walls

    # ============================================================
    # ITERATIONS
    # ============================================================

    def make_iterations(self):

        for _ in range(self.iterations):

            new_grid = [
                ['#' for _ in range(self.width)]
                for _ in range(self.height)
            ]

            for y in range(self.height):

                for x in range(self.width):

                    walls = self.count_walls_around(x, y)

                    # regra clássica
                    if walls >= 5:
                        new_grid[y][x] = '#'
                    else:
                        new_grid[y][x] = '.'

            self.grid = new_grid

    # ============================================================
    # FLOOR DETECTION
    # ============================================================

    def find_floor_tiles(self):

        self.floor_tiles = []

        for y in range(self.height):

            for x in range(self.width):

                if self.grid[y][x] == '.':
                    self.floor_tiles.append((x, y))

    # ============================================================
    # GET NEIGHBORS 
    # ============================================================

    def get_neighbors(self, x, y):

        neighbors = []

        directions = [
            (0, -1),
            (0, 1),
            (-1, 0),
            (1, 0)
        ]

        for dx, dy in directions:

            nx = x + dx
            ny = y + dy

            if (
                0 <= nx < self.width and
                0 <= ny < self.height
            ):

                neighbors.append((nx, ny))

        return neighbors
    
    # ============================================================
    # FLOOD FILL 
    # ============================================================
    
    def flood_fill(self, start_x, start_y, visited):

        stack = [(start_x, start_y)]

        region = []

        while stack:

            x, y = stack.pop()

            if (x, y) in visited:
                continue

            visited.add((x, y))

            if self.grid[y][x] != '.':
                continue

            region.append((x, y))

            for nx, ny in self.get_neighbors(x, y):

                if (nx, ny) not in visited:

                    stack.append((nx, ny))

        return region
    

    # ============================================================
    # FIND REGIONS
    # ============================================================

    def find_regions(self):

        visited = set()

        regions = []

        for y in range(self.height):

            for x in range(self.width):

                if (
                    self.grid[y][x] == '.' and
                    (x, y) not in visited
                ):

                    region = self.flood_fill(
                        x,
                        y,
                        visited
                    )

                    if region:
                        regions.append(region)

        return regions

    # ============================================================
    # KEEP LARGEST REGION
    # ============================================================    

    def keep_largest_region(self):

        regions = self.find_regions()

        if not regions:
            return

        largest_region = max(
            regions,
            key=len
        )

        largest_set = set(largest_region)

        for y in range(self.height):

            for x in range(self.width):

                if (x, y) not in largest_set:
                    self.grid[y][x] = '#'
    
    # ============================================================
    # CONNECTION POINT
    # ============================================================

    def choose_connection_point(self):

        if not self.floor_tiles:
            self.connection_point = None
            return

        # pode melhorar depois
        self.connection_point = self.rng.choice(
            self.floor_tiles
        )

    # ============================================================
    # PIPELINE
    # ============================================================

    def generate(self):

        self.generate_random()

        self.make_iterations()

        self.keep_largest_region()

        self.find_floor_tiles()

        self.choose_connection_point()

    # ============================================================
    # DEBUG
    # ============================================================

    def print_map(self):

        for row in self.grid:
            print("".join(row))
