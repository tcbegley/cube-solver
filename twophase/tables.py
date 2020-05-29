import json
import os

from .cubes.cubiecube import MOVE_CUBE, CubieCube


class PruningTable:
    """
    Helper class to allow pruning to be used as though they were 2-D tables
    """

    def __init__(self, table, stride):
        self.table = table
        self.stride = stride

    def __getitem__(self, x):
        return self.table[x[0] * self.stride + x[1]]


class Tables:
    """
    Class for holding move and pruning tables in memory.

    Move tables are used for updating coordinate representation of cube when a
    particular move is applied.

    Pruning tables are used to obtain lower bounds for the number of moves
    required to reach a solution given a particular pair of coordinates.
    """

    _tables_loaded = False

    # 3^7 possible corner orientations
    TWIST = 2187
    # 2^11 possible edge flips
    FLIP = 2048
    # 12C4 possible positions of FR, FL, BL, BR
    UDSLICE = 495
    # 4! possible permutations of FR, FL, BL, BR
    EDGE4 = 24
    # 8! possible permutations of UR, UF, UL, UB, DR, DF, DL, DB in phase two
    EDGE8 = 40320
    # 8! possible permutations of the corners
    CORNER = 40320
    # 12! possible permutations of all edges
    EDGE = 479001600
    # 6*3 possible moves
    MOVES = 18

    def __init__(self):
        if not self._tables_loaded:
            self.load_tables()

    @classmethod
    def load_tables(cls):
        if os.path.isfile("tables.json"):
            with open("tables.json", "r") as f:
                tables = json.load(f)
            cls.twist_move = tables["twist_move"]
            cls.flip_move = tables["flip_move"]
            cls.udslice_move = tables["udslice_move"]
            cls.edge4_move = tables["edge4_move"]
            cls.edge8_move = tables["edge8_move"]
            cls.corner_move = tables["corner_move"]
            cls.udslice_twist_prune = PruningTable(
                tables["udslice_twist_prune"], cls.TWIST
            )
            cls.udslice_flip_prune = PruningTable(
                tables["udslice_flip_prune"], cls.FLIP
            )
            cls.edge4_edge8_prune = PruningTable(
                tables["edge4_edge8_prune"], cls.EDGE8
            )
            cls.edge4_corner_prune = PruningTable(
                tables["edge4_corner_prune"], cls.CORNER
            )
        else:
            # ----------  Phase 1 move tables  ---------- #
            cls.twist_move = cls.make_twist_table()
            cls.flip_move = cls.make_flip_table()
            cls.udslice_move = cls.make_udslice_table()

            # ----------  Phase 2 move tables  ---------- #
            cls.edge4_move = cls.make_edge4_table()
            cls.edge8_move = cls.make_edge8_table()
            cls.corner_move = cls.make_corner_table()

            # ----------  Phase 1 pruning tables  ---------- #
            cls.udslice_twist_prune = cls.make_udslice_twist_prune()
            cls.udslice_flip_prune = cls.make_udslice_flip_prune()

            # --------  Phase 2 pruning tables  ---------- #
            cls.edge4_edge8_prune = cls.make_edge4_edge8_prune()
            cls.edge4_corner_prune = cls.make_edge4_corner_prune()

            tables = {
                "twist_move": cls.twist_move,
                "flip_move": cls.flip_move,
                "udslice_move": cls.udslice_move,
                "edge4_move": cls.edge4_move,
                "edge8_move": cls.edge8_move,
                "corner_move": cls.corner_move,
                "udslice_twist_prune": cls.udslice_twist_prune.table,
                "udslice_flip_prune": cls.udslice_flip_prune.table,
                "edge4_edge8_prune": cls.edge4_edge8_prune.table,
                "edge4_corner_prune": cls.edge4_corner_prune.table,
            }
            with open("tables.json", "w") as f:
                json.dump(tables, f)

        cls._tables_loaded = True

    @classmethod
    def make_twist_table(cls):
        twist_move = [[0] * cls.MOVES for i in range(cls.TWIST)]
        a = CubieCube()
        for i in range(cls.TWIST):
            a.twist = i
            for j in range(6):
                for k in range(3):
                    a.corner_multiply(MOVE_CUBE[j])
                    twist_move[i][3 * j + k] = a.twist
                a.corner_multiply(MOVE_CUBE[j])
        return twist_move

    @classmethod
    def make_flip_table(cls):
        flip_move = [[0] * cls.MOVES for i in range(cls.FLIP)]
        a = CubieCube()
        for i in range(cls.FLIP):
            a.flip = i
            for j in range(6):
                for k in range(3):
                    a.edge_multiply(MOVE_CUBE[j])
                    flip_move[i][3 * j + k] = a.flip
                a.edge_multiply(MOVE_CUBE[j])
        return flip_move

    @classmethod
    def make_udslice_table(cls):
        udslice_move = [[0] * cls.MOVES for i in range(cls.UDSLICE)]
        a = CubieCube()
        for i in range(cls.UDSLICE):
            a.udslice = i
            for j in range(6):
                for k in range(3):
                    a.edge_multiply(MOVE_CUBE[j])
                    udslice_move[i][3 * j + k] = a.udslice
                a.edge_multiply(MOVE_CUBE[j])
        return udslice_move

    @classmethod
    def make_edge4_table(cls):
        edge4_move = [[0] * cls.MOVES for i in range(cls.EDGE4)]
        a = CubieCube()
        for i in range(cls.EDGE4):
            a.edge4 = i
            for j in range(6):
                for k in range(3):
                    a.edge_multiply(MOVE_CUBE[j])
                    if k % 2 == 0 and j % 3 != 0:
                        edge4_move[i][3 * j + k] = -1
                    else:
                        edge4_move[i][3 * j + k] = a.edge4
                a.edge_multiply(MOVE_CUBE[j])
        return edge4_move

    @classmethod
    def make_edge8_table(cls):
        edge8_move = [[0] * cls.MOVES for i in range(cls.EDGE8)]
        a = CubieCube()
        for i in range(cls.EDGE8):
            a.edge8 = i
            for j in range(6):
                for k in range(3):
                    a.edge_multiply(MOVE_CUBE[j])
                    if k % 2 == 0 and j % 3 != 0:
                        edge8_move[i][3 * j + k] = -1
                    else:
                        edge8_move[i][3 * j + k] = a.edge8
                a.edge_multiply(MOVE_CUBE[j])
        return edge8_move

    @classmethod
    def make_corner_table(cls):
        corner_move = [[0] * cls.MOVES for i in range(cls.CORNER)]
        a = CubieCube()
        for i in range(cls.CORNER):
            a.corner = i
            for j in range(6):
                for k in range(3):
                    a.corner_multiply(MOVE_CUBE[j])
                    if k % 2 == 0 and j % 3 != 0:
                        corner_move[i][3 * j + k] = -1
                    else:
                        corner_move[i][3 * j + k] = a.corner
                a.corner_multiply(MOVE_CUBE[j])
        return corner_move

    @classmethod
    def make_udslice_twist_prune(cls):
        udslice_twist_prune = [-1] * (cls.UDSLICE * cls.TWIST)
        udslice_twist_prune[0] = 0
        count, depth = 1, 0
        while count < cls.UDSLICE * cls.TWIST:
            for i in range(cls.UDSLICE * cls.TWIST):
                if udslice_twist_prune[i] == depth:
                    m = [
                        cls.udslice_move[i // cls.TWIST][j] * cls.TWIST
                        + cls.twist_move[i % cls.TWIST][j]
                        for j in range(18)
                    ]
                    for x in m:
                        if udslice_twist_prune[x] == -1:
                            count += 1
                            udslice_twist_prune[x] = depth + 1
            depth += 1
        return PruningTable(udslice_twist_prune, cls.TWIST)

    @classmethod
    def make_udslice_flip_prune(cls):
        udslice_flip_prune = [-1] * (cls.UDSLICE * cls.FLIP)
        udslice_flip_prune[0] = 0
        count, depth = 1, 0
        while count < cls.UDSLICE * cls.FLIP:
            for i in range(cls.UDSLICE * cls.FLIP):
                if udslice_flip_prune[i] == depth:
                    m = [
                        cls.udslice_move[i // cls.FLIP][j] * cls.FLIP
                        + cls.flip_move[i % cls.FLIP][j]
                        for j in range(18)
                    ]
                    for x in m:
                        if udslice_flip_prune[x] == -1:
                            count += 1
                            udslice_flip_prune[x] = depth + 1
            depth += 1
        return PruningTable(udslice_flip_prune, cls.FLIP)

    @classmethod
    def make_edge4_edge8_prune(cls):
        edge4_edge8_prune = [-1] * (cls.EDGE4 * cls.EDGE8)
        edge4_edge8_prune[0] = 0
        count, depth = 1, 0
        while count < cls.EDGE4 * cls.EDGE8:
            for i in range(cls.EDGE4 * cls.EDGE8):
                if edge4_edge8_prune[i] == depth:
                    m = [
                        cls.edge4_move[i // cls.EDGE8][j] * cls.EDGE8
                        + cls.edge8_move[i % cls.EDGE8][j]
                        for j in range(18)
                    ]
                    for x in m:
                        if edge4_edge8_prune[x] == -1:
                            count += 1
                            edge4_edge8_prune[x] = depth + 1
            depth += 1
        return PruningTable(edge4_edge8_prune, cls.EDGE8)

    @classmethod
    def make_edge4_corner_prune(cls):
        edge4_corner_prune = [-1] * (cls.EDGE4 * cls.CORNER)
        edge4_corner_prune[0] = 0
        count, depth = 1, 0
        while count < cls.EDGE4 * cls.CORNER:
            for i in range(cls.EDGE4 * cls.CORNER):
                if edge4_corner_prune[i] == depth:
                    m = [
                        cls.edge4_move[i // cls.CORNER][j] * cls.CORNER
                        + cls.corner_move[i % cls.CORNER][j]
                        for j in range(18)
                    ]
                    for x in m:
                        if edge4_corner_prune[x] == -1:
                            count += 1
                            edge4_corner_prune[x] = depth + 1
            depth += 1
        return PruningTable(edge4_corner_prune, cls.CORNER)
