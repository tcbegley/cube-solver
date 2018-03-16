"""
Class that represents cube on the coordinate level and constructs move tables.
"""
import json
import os

from .cubie_cube import MOVE_CUBE, CubieCube

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


class CoordCube:
    _tables_loaded = False
    tables = {}

    def __init__(self, c=None):
        cls = self.__class__
        if not cls._tables_loaded:
            cls.load_tables()
        if isinstance(c, CubieCube):
            # initialise from cubiecube c
            self.twist = c.twist
            self.flip = c.flip
            self.udslice = c.udslice
            self.edge4 = c.edge4
            self.edge8 = c.edge8
            self.corner = c.corner
        else:
            # initialise to clean cube
            self.twist = 0
            self.flip = 0
            self.udslice = 0
            self.edge4 = 0
            self.edge8 = 0
            self.corner = 0

    def move(self, mv):
        """
        Update all coordinates after applying move mv using the move tables.

        Parameters
        ----------
        mv : int
            Integer representing one of 18 non-identity face turns. Calulate as
            3 * i + j where i = 0, 1, 2, 3, 4, 5 for U, R, F, D, L, B
            respectively, and j = 0, 1, 2 for quarter turn clockwise, half turn
            and quarter turn anticlockwise respectively.
        """
        cls = self.__class__
        self.twist = cls.tables['twist_move'][self.twist][mv]
        self.flip = cls.tables['flip_move'][self.flip][mv]
        self.udslice = cls.tables['udslice_move'][self.udslice][mv]
        self.edge4 = cls.tables['edge4_move'][self.edge4][mv]
        self.edge8 = cls.tables['edge8_move'][self.edge8][mv]
        self.corner = cls.tables['corner_move'][self.corner][mv]

    @classmethod
    def load_tables(cls):
        if os.path.isfile('tables.json'):
            print("Tables detected, loading from disk...")
            with open('tables.json', 'r') as f:
                cls.tables = json.load(f)
            print("Tables loaded successfully.")
        else:
            # ----------  Phase 1 move tables  ---------- #
            cls.tables['twist_move'] = cls.make_twist_table()
            cls.tables['flip_move'] = cls.make_flip_table()
            cls.tables['udslice_move'] = cls.make_udslice_table()

            # ----------  Phase 2 move tables  ---------- #
            # in phase two, we only allow half-turns of the faces R, F, L, B.
            # quarter turn moves for these faces are replaced with -1.
            cls.tables['edge4_move'] = cls.make_edge4_table()
            cls.tables['edge8_move'] = cls.make_edge8_table()
            cls.tables['corner_move'] = cls.make_corner_table()

            # ----------  Phase 1 pruning tables  ---------- #
            # These tables store estimates for the minimum number of moves
            # required to get from a (slice, twist) coordinate pair
            # (respectively (slice, flip) pair) to reach a phase 2 position.
            # Estimates are conservative (will never overstate).
            cls.tables['udslice_twist_prune'] = cls.make_udslice_twist_prune()
            cls.tables['udslice_flip_prune'] = cls.make_udslice_flip_prune()

            # --------  Phase 2 pruning tables  ---------- #
            # These tables store estimates for the minimum number of moves
            # required to get from a (edge4, edge8) coordinate pair
            # (respectively (edge4, corner) pair) to reach a clean cube.
            # Estimates are conservative (will never overstate).
            cls.tables['edge4_edge8_prune'] = cls.make_edge4_edge8_prune()
            cls.tables['edge4_corner_prune'] = cls.make_edge4_corner_prune()

            print("Saving tables to disk...")
            with open('tables.json', 'w') as f:
                json.dump(cls.tables, f)
            print("Tables saved successfully.")
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
        print("twist_move calculated")
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
        print("flip_move calculated")
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
        print("slice_move calculated")
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
        print("edge4_move calculated")
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
        print("edge8_move calculated")
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
        print("corner_move calculated")
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
                        cls.tables['udslice_move'][i // TWIST][j] * TWIST +
                        cls.tables['twist_move'][i % TWIST][j]
                        for j in range(18)
                    ]
                    for x in m:
                        if udslice_twist_prune[x] == -1:
                            count += 1
                            udslice_twist_prune[x] = depth + 1
            depth += 1
        print("udslice_twist_prune calculated")
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
                        cls.tables['udslice_move'][i // FLIP][j] * FLIP +
                        cls.tables['flip_move'][i % FLIP][j]
                        for j in range(18)
                    ]
                    for x in m:
                        if udslice_flip_prune[x] == -1:
                            count += 1
                            udslice_flip_prune[x] = depth + 1
            depth += 1
        print("udslice_flip_prune calculated")
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
                        cls.tables['edge4_move'][i // EDGE8][j] * EDGE8 +
                        cls.tables['edge8_move'][i % EDGE8][j]
                        for j in range(18)
                    ]
                    for x in m:
                        if edge4_edge8_prune[x] == -1:
                            count += 1
                            edge4_edge8_prune[x] = depth + 1
            depth += 1
        print("edge4_edge8_prune calculated")
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
                        cls.tables['edge4_move'][i // CORNER][j] * CORNER +
                        cls.tables['corner_move'][i % CORNER][j]
                        for j in range(18)
                    ]
                    for x in m:
                        if edge4_corner_prune[x] == -1:
                            count += 1
                            edge4_corner_prune[x] = depth + 1
            depth += 1
        print("edge4_corner_prune calculated")
        return edge4_corner_prune
