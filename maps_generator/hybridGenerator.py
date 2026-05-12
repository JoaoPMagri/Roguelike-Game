import random
from maps_generator.mapGenerator import MapGenerator
from maps_generator.bsp import Bsp
from maps_generator.cellularAutomata import CellularAutomata
from maps_generator.randomWalk import RandomWalk

class HybridGenerator(MapGenerator):
    def __init__(self, width, height, seed,min_leaf_size,density,iterations):
        super().__init__(width, height, seed)
        self.min_leaf_size = min_leaf_size
        self.density = density
        self.iterations = iterations
        
        self.corridors_grid = [
            ['#' for _ in range(width)]
            for _ in range(height)
        ]
    
    def carve_h(self, x1, x2, y):

        for x in range(
            min(x1, x2),
            max(x1, x2) + 1
        ):
            self.corridors_grid[y][x] = '.'

    def carve_v(self, y1, y2, x):

        for y in range(
            min(y1, y2),
            max(y1, y2) + 1
        ):
            self.corridors_grid[y][x] = '.'

    def make_random_path(self):
        mapa = RandomWalk(width=self.width,height=self.height,
                          seed=self.rng.random(),iterations=self.iterations)
        mapa.grid = self.corridors_grid
        mapa.make_iterations()

        for x,y in mapa.get_floors():
            self.grid[y][x] = '.'

    def generate(self): 
        mapa = Bsp(width=self.width,height=self.height,
                   seed=self.rng.random(),min_leaf_size=self.min_leaf_size) 
        mapa.generate_bsp() 
        points = [] 
        for leaf in mapa.leaves: 
            submap = CellularAutomata(width=leaf.width,height=leaf.height, 
                                      seed=self.rng.random(),
                                      density=self.density,iterations=self.iterations) 
            submap.generate() 
            x,y = submap.connection_point 
            point = (x + leaf.x, y + leaf.y) 
            points.append(point) 
            for y in range(leaf.height): 
                for x in range(leaf.width): 
                    gx = x + leaf.x 
                    gy = y + leaf.y 
                    self.grid[gy][gx] = submap.grid[y][x] 
            
        for i in range(len(points)-1): 
            self.connect_points(points[i],points[i+1])
        
        self.make_random_path()
        super().choose_conection_point()
        