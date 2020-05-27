import json
import os

from .cubes.cubiecube import MOVE_CUBE, CubieCube


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
# 6*3 possible moves
MOVES = 18


class Tables:
    """
    Class for holding move and pruning tables in memory.

    Move tables are used for updating coordinate representation of cube when a
    particular move is applied.

    Pruning tables are used to obtain lower bounds for the number of moves
    required to reach a solution given a particular pair of coordinates.
    """

    _tables_loaded = False

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
            cls.udslice_twist_prune = tables["udslice_twist_prune"]
            cls.udslice_flip_prune = tables["udslice_flip_prune"]
            cls.edge4_edge8_prune = tables["edge4_edge8_prune"]
            cls.edge4_corner_prune = tables["edge4_corner_prune"]
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
                "udslice_twist_prune": cls.udslice_twist_prune,
                "udslice_flip_prune": cls.udslice_flip_prune,
                "edge4_edge8_prune": cls.edge4_edge8_prune,
                "edge4_corner_prune": cls.edge4_corner_prune,
            }
            with open("tables.json", "w") as f:
                json.dump(tables, f)

        cls._tables_loaded = True

    @staticmethod
    def make_twist_table():
        twist_move = [[0] * MOVES for i in range(TWIST)]
        a = CubieCube()
        for i in range(TWIST):
            a.twist = i
            for j in range(6):
                for k in range(3):
                    a.corner_multiply(MOVE_CUBE[j])
                    twist_move[i][3 * j + k] = a.twist
                a.corner_multiply(MOVE_CUBE[j])
        return twist_move

    @staticmethod
    def make_flip_table():
        flip_move = [[0] * MOVES for i in range(FLIP)]
        a = CubieCube()
        for i in range(FLIP):
            a.flip = i
            for j in range(6):
                for k in range(3):
                    a.edge_multiply(MOVE_CUBE[j])
                    flip_move[i][3 * j + k] = a.flip
                a.edge_multiply(MOVE_CUBE[j])
        return flip_move

    @staticmethod
    def make_udslice_table():
        udslice_move = [[0] * MOVES for i in range(UDSLICE)]
        a = CubieCube()
        for i in range(UDSLICE):
            a.udslice = i
            for j in range(6):
                for k in range(3):
                    a.edge_multiply(MOVE_CUBE[j])
                    udslice_move[i][3 * j + k] = a.udslice
                a.edge_multiply(MOVE_CUBE[j])
        return udslice_move

    @staticmethod
    def make_edge4_table():
        edge4_move = [[0] * MOVES for i in range(EDGE4)]
        a = CubieCube()
        for i in range(EDGE4):
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

    @staticmethod
    def make_edge8_table():
        edge8_move = [[0] * MOVES for i in range(EDGE8)]
        a = CubieCube()
        for i in range(EDGE8):
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

    @staticmethod
    def make_corner_table():
        corner_move = [[0] * MOVES for i in range(CORNER)]
        a = CubieCube()
        for i in range(CORNER):
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
        udslice_twist_prune = [-1] * (UDSLICE * TWIST)
        udslice_twist_prune[0] = 0
        count, depth = 1, 0
        while count < UDSLICE * TWIST:
            for i in range(UDSLICE * TWIST):
                if udslice_twist_prune[i] == depth:
                    m = [
                        cls.udslice_move[i // TWIST][j] * TWIST
                        + cls.twist_move[i % TWIST][j]
                        for j in range(18)
                    ]
                    for x in m:
                        if udslice_twist_prune[x] == -1:
                            count += 1
                            udslice_twist_prune[x] = depth + 1
            depth += 1
        return udslice_twist_prune

    @classmethod
    def make_udslice_flip_prune(cls):
        udslice_flip_prune = [-1] * (UDSLICE * FLIP)
        udslice_flip_prune[0] = 0
        count, depth = 1, 0
        while count < UDSLICE * FLIP:
            for i in range(UDSLICE * FLIP):
                if udslice_flip_prune[i] == depth:
                    m = [
                        cls.udslice_move[i // FLIP][j] * FLIP
                        + cls.flip_move[i % FLIP][j]
                        for j in range(18)
                    ]
                    for x in m:
                        if udslice_flip_prune[x] == -1:
                            count += 1
                            udslice_flip_prune[x] = depth + 1
            depth += 1
        return udslice_flip_prune

    @classmethod
    def make_edge4_edge8_prune(cls):
        edge4_edge8_prune = [-1] * (EDGE4 * EDGE8)
        edge4_edge8_prune[0] = 0
        count, depth = 1, 0
        while count < EDGE4 * EDGE8:
            for i in range(EDGE4 * EDGE8):
                if edge4_edge8_prune[i] == depth:
                    m = [
                        cls.edge4_move[i // EDGE8][j] * EDGE8
                        + cls.edge8_move[i % EDGE8][j]
                        for j in range(18)
                    ]
                    for x in m:
                        if edge4_edge8_prune[x] == -1:
                            count += 1
                            edge4_edge8_prune[x] = depth + 1
            depth += 1
        return edge4_edge8_prune

    @classmethod
    def make_edge4_corner_prune(cls):
        edge4_corner_prune = [-1] * (EDGE4 * CORNER)
        edge4_corner_prune[0] = 0
        count, depth = 1, 0
        while count < EDGE4 * CORNER:
            for i in range(EDGE4 * CORNER):
                if edge4_corner_prune[i] == depth:
                    m = [
                        cls.edge4_move[i // CORNER][j] * CORNER
                        + cls.corner_move[i % CORNER][j]
                        for j in range(18)
                    ]
                    for x in m:
                        if edge4_corner_prune[x] == -1:
                            count += 1
                            edge4_corner_prune[x] = depth + 1
            depth += 1
        return edge4_corner_prune
