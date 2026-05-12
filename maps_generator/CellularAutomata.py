import random
from maps_generator.mapGenerator import MapGenerator

class CellularAutomata(MapGenerator):
    def __init__(self, width, height, seed,density,iterations):
        super().__init__(width, height, seed)
        self.density = density
        self.iterations = iterations

    def set_random_points(self):
        for y in range(self.height):
            if 1 <= y <= self.height-2:
                for x in range(self.width):
                    if 1 <= x <= self.width-2:
                        if self.rng.random() < self.density:
                            self.grid[y][x] = '.'
    
    
    def make_iterations(self):
        for _ in range(self.iterations):
            new_grid = [
                ['#' for _ in range(self.width)]
                for _ in range(self.height)
            ]

            for y in range(self.height):

                for x in range(self.width):

                    neighbors = super().get_neighbors(x,y)

                    walls = 0
                    aux = 0
                    for i,j in neighbors:
                        if self.grid[j][i] == '#':
                            walls += 1
                        aux += 1
                    
                    
                    walls += 8 - aux

                    if walls >= 5:
                        new_grid[y][x] = '#'
                    else:
                        new_grid[y][x] = '.'

            self.grid = new_grid

    # ==============================================================
    # GET NEIGHBORS (polymorphism)
    # ==============================================================

    def get_neighbors(self,x,y):
        neighbors = set()

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

                neighbors.add((nx, ny))

        return neighbors

    # ==============================================================
    # GET REGIONS
    # ==============================================================

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
    

    def find_regions(self):

        visited = set()

        regions = []

        for y in range(self.height):

            for x in range(self.width):

                if (self.grid[y][x] == '.' and (x, y) not in visited):

                    region = self.flood_fill(x,y,visited)

                    if region:
                        regions.append(region)

        return regions
    
    # ==============================================================
    # CONNECT REGIONS
    # ==============================================================
    
    def connect_regions(self):
        regions = self.find_regions()
        points = []
        regiao = 0
        for region in regions:
            regiao += 1
            point = self.rng.choice(region)
            points.append(point)
        for i in range(len(points)-1):
            super().connect_points(points[i],points[i+1])
        
        print(regiao)
    
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
        

    
    def generate(self):
        self.set_random_points()
        self.make_iterations()
        #self.connect_regions()
        self.keep_largest_region()
        super().choose_conection_point()