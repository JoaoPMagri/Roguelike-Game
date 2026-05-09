import random


class Leaf:

    def __init__(self, x, y, width, height):

        self.x = x
        self.y = y

        self.width = width
        self.height = height

        self.left_child = None
        self.right_child = None

        # conteúdo procedural da leaf
        self.room = None

        self.connection_point = None
        self.floor_tiles = []

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


# ================================================================
# BSP
# ================================================================

class BSP:

    def __init__(
        self,
        width,
        height,
        seed,
        min_leaf_size,
        min_room_size
    ):

        self.width = width
        self.height = height

        self.min_leaf_size = min_leaf_size
        self.min_room_size = min_room_size

        self.rng = random.Random(seed)

        self.grid = [
            ['#' for _ in range(width)]
            for _ in range(height)
        ]

        self.root = None
        self.leaves = []

    # ============================================================
    # BSP GENERATION
    # ============================================================

    def generate_bsp(self):

        self.root = Leaf(
            0,
            0,
            self.width,
            self.height
        )

        leaves = [self.root]

        did_split = True

        while did_split:

            did_split = False
            new_leaves = []

            for leaf in leaves:

                if leaf.split(
                    self.min_leaf_size,
                    self.rng
                ):

                    new_leaves.append(
                        leaf.left_child
                    )

                    new_leaves.append(
                        leaf.right_child
                    )

                    did_split = True

                else:
                    new_leaves.append(leaf)

            leaves = new_leaves

        self.leaves = leaves

    # ============================================================
    # BSP ROOM GENERATION
    # ============================================================

    def generate_bsp_room(self, leaf):
        room_w = self.rng.randint(
            self.min_room_size,
            leaf.width - 2
        )

        room_h = self.rng.randint(
            self.min_room_size,
            leaf.height - 2
        )

        room_x = self.rng.randint(
            leaf.x + 1,
            leaf.x + leaf.width - room_w - 1
        )

        room_y = self.rng.randint(
            leaf.y + 1,
            leaf.y + leaf.height - room_h - 1
        )

        leaf.room = (
            room_x,
            room_y,
            room_w,
            room_h
        )

        floor_tiles = []

        for y in range(room_y, room_y + room_h):

            for x in range(room_x, room_x + room_w):

                self.grid[y][x] = '.'

                floor_tiles.append((x, y))

        leaf.floor_tiles = floor_tiles

        # centro da sala
        leaf.connection_point = (
            room_x + room_w // 2,
            room_y + room_h // 2
        )

    # ============================================================
    # CONTENT GENERATION
    # ============================================================

    def generate_leaf_contents(self):

        for leaf in self.leaves:
            self.generate_bsp_room(leaf)

    # ============================================================
    # CORRIDORS
    # ============================================================

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

    # ============================================================
    # TREE CONNECTION
    # ============================================================

    def get_connection_point(self, leaf):

        # leaf final
        if leaf.connection_point is not None:
            return leaf.connection_point

        points = []

        if leaf.left_child:
            points.append(
                self.get_connection_point(
                    leaf.left_child
                )
            )

        if leaf.right_child:
            points.append(
                self.get_connection_point(
                    leaf.right_child
                )
            )

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

        self.connect_points(
            left_point,
            right_point
        )

        self.connect_tree(leaf.left_child)
        self.connect_tree(leaf.right_child)

    # ============================================================
    # PIPELINE
    # ============================================================

    def generate(self):

        self.generate_bsp()

        self.generate_leaf_contents()

        self.connect_tree(self.root)

    # ============================================================
    # DEBUG
    # ============================================================

    def print_map(self):

        for row in self.grid:
            print("".join(row))