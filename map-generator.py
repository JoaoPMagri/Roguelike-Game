import random

MAP_WIDTH = 40
MAP_HEIGHT = 12
MIN_LEAF_SIZE = 5
MIN_ROOM_SIZE = 3

mapa = [['#' for x in range(MAP_WIDTH)] for y in range(MAP_HEIGHT)]

class Leaf:
    def __init__(self, x, y, width, height):
        self.x, self.y = x, y
        self.width, self.height = width, height
        self.left_child = None
        self.right_child = None
        self.room = None

    def split(self):
        # Não divide se já estiver no tamanho mínimo
        if self.width <= MIN_LEAF_SIZE * 2 and self.height <= MIN_LEAF_SIZE * 2:
            return False

        # Escolhe a direção da divisão
        split_h = random.choice([True, False])

        if self.width > self.height and self.width / self.height >= 1.25:
            split_h = False
        elif self.height > self.width and self.height / self.width >= 1.25:
            split_h = True

        max_value = (self.height if split_h else self.width) - MIN_LEAF_SIZE
        if max_value <= MIN_LEAF_SIZE:
            return False

        split_value = random.randint(MIN_LEAF_SIZE, max_value)

        if split_h:
            self.left_child = Leaf(self.x, self.y, self.width, split_value)
            self.right_child = Leaf(self.x, self.y + split_value, self.width, self.height - split_value)
        else:
            self.left_child = Leaf(self.x, self.y, split_value, self.height)
            self.right_child = Leaf(self.x + split_value, self.y, self.width - split_value, self.height)

        return True


def create_bsp(root):
    leaves = [root]
    did_split = True

    while did_split:
        did_split = False
        new_leaves = []
        for leaf in leaves:
            if leaf.split():
                new_leaves.append(leaf.left_child)
                new_leaves.append(leaf.right_child)
                did_split = True
            else:
                new_leaves.append(leaf)
        leaves = new_leaves

    return leaves


def create_room(leaf):
    room_w = random.randint(MIN_ROOM_SIZE, leaf.width - 2)
    room_h = random.randint(MIN_ROOM_SIZE, leaf.height - 2)
    room_x = random.randint(leaf.x + 1, leaf.x + leaf.width - room_w - 1)
    room_y = random.randint(leaf.y + 1, leaf.y + leaf.height - room_h - 1)
    leaf.room = (room_x, room_y, room_w, room_h)

    for y in range(room_y, room_y + room_h):
        for x in range(room_x, room_x + room_w):
            mapa[y][x] = '.'

def connect_rooms(room1, room2):
    x1, y1 = room1[0] + room1[2] // 2, room1[1] + room1[3] // 2
    x2, y2 = room2[0] + room2[2] // 2, room2[1] + room2[3] // 2

    # Corredor em L
    if random.random() < 0.5:
        carve_h(x1, x2, y1)
        carve_v(y1, y2, x2)
    else:
        carve_v(y1, y2, x1)
        carve_h(x1, x2, y2)


def carve_h(x1, x2, y):
    for x in range(min(x1, x2), max(x1, x2) + 1):
        mapa[y][x] = '.'


def carve_v(y1, y2, x):
    for y in range(min(y1, y2), max(y1, y2) + 1):
        mapa[y][x] = '.'


root = Leaf(0, 0, MAP_WIDTH, MAP_HEIGHT)
leaves = create_bsp(root)

rooms = []
for leaf in leaves:
    create_room(leaf)
    rooms.append(leaf.room)

for i in range(len(rooms) - 1):
    connect_rooms(rooms[i], rooms[i + 1])

for row in mapa:
    print("".join(row))