import random
from maps_generator.mapGenerator import MapGenerator

class Leaf:

    def __init__(self, x, y, width, height):

        self.x = x
        self.y = y

        self.width = width
        self.height = height

        self.left_child = None
        self.right_child = None

        self.room = None

        self.connection_point = None

    # ============================================================
    # BSP SPLIT
    # ============================================================

    def split(self, min_leaf_size, rng):

        if (
            self.width <= min_leaf_size * 2 and
            self.height <= min_leaf_size * 2
        ):
            return False

        split_h = rng.choice([True, False])

        # força direção mais apropriada
        if self.width > self.height and self.width / self.height >= 1.25:
            split_h = False

        elif self.height > self.width and self.height / self.width >= 1.25:
            split_h = True

        max_value = (
            self.height if split_h else self.width
        ) - min_leaf_size

        if max_value <= min_leaf_size:
            return False

        split_value = rng.randint(min_leaf_size, max_value)

        if split_h:

            self.left_child = Leaf(
                self.x,
                self.y,
                self.width,
                split_value
            )

            self.right_child = Leaf(
                self.x,
                self.y + split_value,
                self.width,
                self.height - split_value
            )

        else:

            self.left_child = Leaf(
                self.x,
                self.y,
                split_value,
                self.height
            )

            self.right_child = Leaf(
                self.x + split_value,
                self.y,
                self.width - split_value,
                self.height
            )

        return True

class Bsp(MapGenerator):
    def __init__(self, width, height, seed,min_leaf_size):
        super().__init__(width, height, seed)
        self.min_leaf_size = min_leaf_size
        self.root = None
        self.leaves = []

    def generate_bsp(self):
        self.root = Leaf(0,0,self.width,self.height)

        leaves = [self.root]

        did_split = True

        while did_split:

            did_split = False
            new_leaves = []

            for leaf in leaves:
                if leaf.split(self.min_leaf_size,self.rng):
                    new_leaves.append(leaf.left_child)
                    new_leaves.append(leaf.right_child)
                    did_split = True
                else:
                    new_leaves.append(leaf)
            leaves = new_leaves
        self.leaves = leaves

    
    def generate_bsp_room(self, leaf):
        room_w = self.rng.randint(self.min_leaf_size - 2,leaf.width - 2)
        room_h = self.rng.randint(self.min_leaf_size - 2,leaf.height - 2)
        room_x = self.rng.randint(leaf.x + 1,leaf.x + leaf.width - room_w - 1)
        room_y = self.rng.randint(leaf.y + 1,leaf.y + leaf.height - room_h - 1)

        leaf.room = (room_x,room_y,room_w,room_h)

        for y in range(room_y, room_y + room_h):

            for x in range(room_x, room_x + room_w):

                self.grid[y][x] = '.'

        # centro da sala
        leaf.connection_point = (room_x + room_w // 2,room_y + room_h // 2)
      
    def generate(self):
        self.generate_bsp()
        points = []
        for leaf in self.leaves:
            self.generate_bsp_room(leaf)
            points.append(leaf.connection_point)
        
        for i in range(len(points) - 1):
            self.connect_points(points[i],points[i+1])
        
        super().choose_conection_point()
