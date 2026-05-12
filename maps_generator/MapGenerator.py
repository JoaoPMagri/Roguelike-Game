import random

class MapGenerator:
    def __init__(self,width,height,seed):
        self.width = width
        self.height = height
        self.rng = random.Random(seed)
        self.connection_point = None
        self.world_x = 0
        self.world_y = 0

        self.grid = [
            ['#' for _ in range(width)]
            for _ in range(height)
        ]
    
    def get_floors(self):
        floors = set()
        for y in range(self.height):
            for x in range(self.width):
                if self.grid[y][x] == '.':
                    floors.add((x,y))
        
        return floors
    
    def get_neighbors(self,x,y):
        neighbors = set()

        directions = [
            (-1,1),
            (1,-1),
            (-1,-1),
            (1, 1),
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
    
    def get_walls(self):
        walls = set()

        floors = self.get_floors()

        for x,y in floors:
            neighbors = MapGenerator.get_neighbors(self,x,y)
            for x2,y2 in neighbors:
                if (x2,y2) in walls:
                    continue
                elif self.grid[y2][x2] == '#':
                    walls.add((x2,y2))
        
        return walls


    def choose_conection_point(self):
        floors = list(self.get_floors())
        self.connection_point =  self.rng.choice(floors)
    
    def carve_h(self, x1, x2, y):

        for x in range(
            min(x1, x2),
            max(x1, x2) + 1
        ):

            self.grid[y][x] = '.'

    def carve_v(self, y1, y2, x):

        for y in range(
            min(y1, y2),
            max(y1, y2) + 1
        ):

            self.grid[y][x] = '.'
    
    def connect_points(self, p1, p2):

        x1, y1 = p1
        x2, y2 = p2

        if self.rng.random() < 0.5:

            self.carve_h(x1, x2, y1)

            self.carve_v(y1, y2, x2)

        else:

            self.carve_v(y1, y2, x1)

            self.carve_h(x1, x2, y2)
    
    def join_maps(self,maps):

        current_x = 0
        current_y = 0

        row_height = 0
        points = []
        for submap in maps:

            # quebra linha se não couber
            if current_x + submap.width > self.width:

                current_x = 0
                current_y += row_height

                row_height = 0

            # verifica altura
            if current_y + submap.height > self.height:

                raise ValueError(
                    "Mapa não cabe dentro do mapa principal"
                )

            # copia tiles
            for y in range(submap.height):
                for x in range(submap.width):
                    self.grid[current_y + y][current_x + x] = submap.grid[y][x]

            # salva posição global
            submap.world_x = current_x
            submap.world_y = current_y

            # avança cursor
            current_x += submap.width

            # atualiza altura da linha
            row_height = max(row_height, submap.height)
            x,y = submap.connection_point
            points.append((x + submap.world_x,y + submap.world_y))
        
        for i in range(len(points)-1):
            self.connect_points(points[i],points[i+1])

    def print_map(self):
        for row in self.grid:
            print("".join(row))