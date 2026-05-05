import random

class Leaf:
    def __init__(self, x, y, width, height):
        self.x, self.y = x, y
        self.width, self.height = width, height
        self.left_child = None
        self.right_child = None
        self.room = None

    def split(self, min_leaf_size, rng):
        if self.width <= min_leaf_size * 2 and self.height <= min_leaf_size * 2:
            return False

        split_h = rng.choice([True, False])

        if self.width > self.height and self.width / self.height >= 1.25:
            split_h = False
        elif self.height > self.width and self.height / self.width >= 1.25:
            split_h = True

        max_value = (self.height if split_h else self.width) - min_leaf_size
        if max_value <= min_leaf_size:
            return False

        split_value = rng.randint(min_leaf_size, max_value)

        if split_h:
            self.left_child = Leaf(self.x, self.y, self.width, split_value)
            self.right_child = Leaf(self.x, self.y + split_value, self.width, self.height - split_value)
        else:
            self.left_child = Leaf(self.x, self.y, split_value, self.height)
            self.right_child = Leaf(self.x + split_value, self.y, self.width - split_value, self.height)

        return True


class Map:
    def __init__(self, width=40, height=20, seed=None,
                 min_leaf_size=8, min_room_size=3):

        self.width = width
        self.height = height
        self.min_leaf_size = min_leaf_size
        self.min_room_size = min_room_size

        self.rng = random.Random(seed)  

        self.grid = [['#' for _ in range(width)] for _ in range(height)]
        self.leaves = []
        self.rooms = []

    # ================= BSP =================

    def generate_bsp(self):
        root = Leaf(0, 0, self.width, self.height)
        leaves = [root]

        did_split = True
        while did_split:
            did_split = False
            new_leaves = []

            for leaf in leaves:
                if leaf.split(self.min_leaf_size, self.rng):
                    new_leaves.append(leaf.left_child)
                    new_leaves.append(leaf.right_child)
                    did_split = True
                else:
                    new_leaves.append(leaf)

            leaves = new_leaves

        self.leaves = leaves

    # ================= ROOMS =================

    def create_room(self, leaf):
        room_w = self.rng.randint(self.min_room_size, leaf.width - 2)
        room_h = self.rng.randint(self.min_room_size, leaf.height - 2)

        room_x = self.rng.randint(leaf.x + 1, leaf.x + leaf.width - room_w - 1)
        room_y = self.rng.randint(leaf.y + 1, leaf.y + leaf.height - room_h - 1)

        leaf.room = (room_x, room_y, room_w, room_h)

        for y in range(room_y, room_y + room_h):
            for x in range(room_x, room_x + room_w):
                self.grid[y][x] = '.'

        self.rooms.append(leaf.room)

    def create_rooms(self):
        for leaf in self.leaves:
            self.create_room(leaf)

    # ================= CORRIDORS =================

    def connect_rooms(self, room1, room2):
        x1, y1 = room1[0] + room1[2] // 2, room1[1] + room1[3] // 2
        x2, y2 = room2[0] + room2[2] // 2, room2[1] + room2[3] // 2

        if self.rng.random() < 0.5:
            self.carve_h(x1, x2, y1)
            self.carve_v(y1, y2, x2)
        else:
            self.carve_v(y1, y2, x1)
            self.carve_h(x1, x2, y2)

    def connect_all_rooms(self):
        for i in range(len(self.rooms) - 1):
            self.connect_rooms(self.rooms[i], self.rooms[i + 1])

    def carve_h(self, x1, x2, y):
        for x in range(min(x1, x2), max(x1, x2) + 1):
            self.grid[y][x] = '.'

    def carve_v(self, y1, y2, x):
        for y in range(min(y1, y2), max(y1, y2) + 1):
            self.grid[y][x] = '.'

    # ================= PIPELINE =================

    def generate(self):
        self.generate_bsp()
        self.create_rooms()
        self.connect_all_rooms()

    # ================= DEBUG =================

    def print_map(self):
        for row in self.grid:
            print("".join(row))
