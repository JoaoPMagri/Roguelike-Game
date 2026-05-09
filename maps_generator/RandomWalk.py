import random


class RandomWalk:

    def __init__(
        self,
        width,
        height,
        iterations,
        seed
    ):

        self.width = width
        self.height = height

        self.iterations = iterations

        self.rng = random.Random(seed)

        self.grid = [
            ['#' for _ in range(width)]
            for _ in range(height)
        ]

        # padronização
        self.floor_tiles = []
        self.connection_point = None

    # ============================================================
    # GET FLOORS
    # ============================================================

    def get_floors(self):
        floor_set = set()

        for y in range(self.height):
            for x in range(self.width):
                if self.grid[y][x] == '.':
                    floor_set.add((x, y))
        
        self.floor_tiles = list(floor_set)

    # ============================================================
    # WALK
    # ============================================================

    def walk(self,x,y):
        for _ in range(self.iterations):

            moves = []

            if y > 1:
                moves.append((0, -1))

            if y < self.height - 2:
                moves.append((0, 1))

            if x > 1:
                moves.append((-1, 0))

            if x < self.width - 2:
                moves.append((1, 0))

            dx, dy = self.rng.choice(moves)

            x += dx
            y += dy

            self.grid[y][x] = '.'

    # ============================================================
    # MULTI WALK
    # ============================================================

    def multi_walk(self):
        self.get_floors()

        for floor in self.floor_tiles:
            x,y = floor
            self.walk(x=x,y=y)
        
        self.get_floors()


    # ============================================================
    # CONNECTION POINT
    # ============================================================

    def choose_connection_point(self):

        if not self.floor_tiles:
            self.connection_point = None
            return

        self.connection_point = self.rng.choice(
            self.floor_tiles
        )


    # ============================================================
    # PIPELINE
    # ============================================================

    def generate(self):

        # começa no centro
        x = self.width // 2
        y = self.height // 2
        self.grid[y][x] = '.'

        self.walk(x=x,y=y)

        self.get_floors()

        self.choose_connection_point()

    # ============================================================
    # DEBUG
    # ============================================================

    def print_map(self):

        for row in self.grid:
            print("".join(row))