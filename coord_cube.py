"""
Class that represents cube on the coordinate level and constructs move tables.
"""

import os
import pickle

from cubie_cube import MOVE_CUBE, CubieCube

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
        """
        cls = self.__class__
        self.twist = cls.tables['twist_move'][self.twist][mv]
        self.flip = cls.tables['flip_move'][self.flip][mv]
        self.udslice = cls.tables['slice_move'][self.udslice][mv]
        self.edge4 = cls.tables['edge4_move'][self.edge4][mv]
        self.edge8 = cls.tables['edge8_move'][self.edge8][mv]
        self.corner = cls.tables['corner_move'][self.corner][mv]

    @classmethod
    def load_tables(cls):
        table_names = (
            'twist_move', 'flip_move', 'slice_move',
            'edge4_move', 'edge8_move', 'corner_move',
            'slice_twist_prun', 'slice_flip_prun',
            'edge4_edge8_prun', 'edge4_corner_prun'
        )
        if os.path.isfile('tables.pkl'):
            print("Tables detected, loading from disk...")
            with open('tables.pkl', 'rb') as f:
                cls.tables = zip(table_names, pickle.load(f))
            print("Tables loaded successfully.")
        else:
            # ----------  Phase 1 move tables  ---------- #
            cls.tables['twist_move'] = cls.make_twist_table()
            cls.tables['flip_move'] = cls.make_flip_table()
            cls.tables['slice_move'] = cls.make_slice_table()

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
            cls.tables['slice_twist_prun'] = cls.make_slice_twist_prun()
            cls.tables['slice_flip_prun'] = cls.make_slice_flip_prun()

            # --------  Phase 2 pruning tables  ---------- #
            # These tables store estimates for the minimum number of moves
            # required to get from a (edge4, edge8) coordinate pair
            # (respectively (edge4, corner) pair) to reach a clean cube.
            # Estimates are conservative (will never overstate).
            cls.tables['edge4_edge8_prun'] = cls.make_edge4_edge8_prun()
            cls.tables['edge4_corner_prun'] = cls.make_edge4_corner_prun()

            print("Saving tables to disk...")
            with open('tables.pkl', 'wb') as f:
                pickle.dump(
                    [cls.tables[table_name] for table_name in table_names], f
                )
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
    def make_slice_table():
        slice_move = [[0] * MOVES for i in range(UDSLICE)]
        a = CubieCube()
        for i in range(UDSLICE):
            a.udslice = i
            for j in range(6):
                for k in range(3):
                    a.edge_multiply(MOVE_CUBE[j])
                    slice_move[i][3 * j + k] = a.udslice
                a.edge_multiply(MOVE_CUBE[j])
        print("slice_move calculated")
        return slice_move

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
    def make_slice_twist_prun(cls):
        slice_twist_prun = [-1] * (UDSLICE * TWIST)
        slice_twist_prun[0] = 0
        count, depth = 1, 0
        while count < UDSLICE * TWIST:
            for i in range(UDSLICE * TWIST):
                if slice_twist_prun[i] == depth:
                    m = [
                        cls.tables['slice_move'][i // TWIST][j] * TWIST +
                        cls.tables['twist_move'][i % TWIST][j]
                        for j in range(18)
                    ]
                    for x in m:
                        if slice_twist_prun[x] == -1:
                            count += 1
                            slice_twist_prun[x] = depth + 1
            depth += 1
        print("slice_twist_prun calculated")
        return slice_twist_prun

    @classmethod
    def make_slice_flip_prun(cls):
        slice_flip_prun = [-1] * (UDSLICE * FLIP)
        slice_flip_prun[0] = 0
        count, depth = 1, 0
        while count < UDSLICE * FLIP:
            for i in range(UDSLICE * FLIP):
                if slice_flip_prun[i] == depth:
                    m = [
                        cls.tables['slice_move'][i // FLIP][j] * FLIP +
                        cls.tables['flip_move'][i % FLIP][j]
                        for j in range(18)
                    ]
                    for x in m:
                        if slice_flip_prun[x] == -1:
                            count += 1
                            slice_flip_prun[x] = depth + 1
            depth += 1
        print("slice_flip_prun calculated")
        return slice_flip_prun

    @classmethod
    def make_edge4_edge8_prun(cls):
        edge4_edge8_prun = [-1] * (EDGE4 * EDGE8)
        edge4_edge8_prun[0] = 0
        count, depth = 1, 0
        while count < EDGE4 * EDGE8:
            for i in range(EDGE4 * EDGE8):
                if edge4_edge8_prun[i] == depth:
                    m = [
                        cls.tables['edge4_move'][i // EDGE8][j] * EDGE8 +
                        cls.tables['edge8_move'][i % EDGE8][j]
                        for j in range(18)
                    ]
                    for x in m:
                        if edge4_edge8_prun[x] == -1:
                            count += 1
                            edge4_edge8_prun[x] = depth + 1
            depth += 1
        print("edge4_edge8_prun calculated")
        return edge4_edge8_prun

    @classmethod
    def make_edge4_corner_prun(cls):
        edge4_corner_prun = [-1] * (EDGE4 * CORNER)
        edge4_corner_prun[0] = 0
        count, depth = 1, 0
        while count < EDGE4 * CORNER:
            for i in range(EDGE4 * CORNER):
                if edge4_corner_prun[i] == depth:
                    m = [
                        cls.tables['edge4_move'][i // CORNER][j] * CORNER +
                        cls.tables['corner_move'][i % CORNER][j]
                        for j in range(18)
                    ]
                    for x in m:
                        if edge4_corner_prun[x] == -1:
                            count += 1
                            edge4_corner_prun[x] = depth + 1
            depth += 1
        print("edge4_corner_prun calculated")
        return edge4_corner_prun
