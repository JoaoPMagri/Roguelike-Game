import random
from maps_generator.mapGenerator import MapGenerator

class RandomWalk(MapGenerator):
    def __init__(self, width, height, seed, iterations):
        super().__init__(width, height, seed)
        self.iterations = iterations
    
    def make_iterations(self):
        floors = super().get_floors()
        for x,y in floors:
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
    
    def generate(self):
        x = self.width//2
        y = self.height//2
        self.grid[y][x] = '.'

        self.make_iterations()
        super().choose_conection_point()