import time

from . import color
from .coord_cube import CORNER, EDGE8, FLIP, TWIST, CoordCube
from .cubie_cube import MOVE_CUBE
from .face_cube import FaceCube


class Solver:
    def __init__(self, max_length=25):
        self.max_length = max_length

    def solve(
        self,
        facelets="UUUUUUUUURRRRRRRRRFFFFFFFFFDDDDDDDDDLLLLLLLLLBBBBBBBBB",
        timeout=10,
    ):
        """
        Solve the cube.

        This method implements back to back IDA* searches for phase 1 and phase
        2. Once the first solution has been found the algorithm checks for
        shorter solutions, including checking whether there is a shorter
        overall solution with a longer first phase.

        Parameters
        ----------
        facelets: str
            Starting position of the cube. Should be a 54 character string
            specifying the stickers on each face (in order U R F D L B),
            reading row by row from the top left hand corner to the bottom
            right.
        timeout: int, optional
            Limit the amount of time search is run for. Default is 10 seconds.
            If max_length is left at the default value of 25, then a solution
            will almost certainly be found almost instantly. However once a
            solution has been found, the algorithm continues to search for
            shorter solutions which takes longer as the search space is
            constrained.
        """
        self.facelets = facelets.upper()
        status = self.verify()
        if status:
            error_message = {
                -1: "each colour should appear exactly 9 times",
                -2: "not all edges exist exactly once",
                -3: "one edge should be flipped",
                -4: "not all corners exist exactly once",
                -5: "one corner should be twisted",
                -6: "two corners or edges should be exchanged",
            }
            raise ValueError("Invalid cube: {}".format(error_message[status]))

        # prepare for phase 1
        self._phase_1_initialise()

        self.timeout = timeout
        self.t_start = time.time()
        self._allowed_length = self.max_length

        while time.time() - self.t_start <= self.timeout:
            solution_not_found = True
            for depth in range(self._allowed_length):
                n = self._phase_1_search(0, depth)
                if n >= 0:
                    solution_not_found = False
                    print(self._solution_to_string(n))
                    self._allowed_length = n - 1
                    break
                if n == -2:
                    # this is a bit ugly, need a better way of ending the
                    # search at timeout that doesn't misreport that the
                    # shortest possible solution has been found.
                    solution_not_found = False
                    print("Reached time limit, ending search.")
                    break
            if solution_not_found:
                print("No shorter solution found.")
                break

    def verify(self):
        count = [0] * 6
        try:
            for char in self.facelets:
                count[color.COLORS[char]] += 1
        except (IndexError, ValueError):
            return -1
        for i in range(6):
            if count[i] != 9:
                return -1

        fc = FaceCube(self.facelets)
        cc = fc.to_cubiecube()

        return cc.verify()

    def _phase_1_initialise(self):
        # the lists 'axis' and 'power' will store the nth move (index of face
        # being turned stored in axis, number of clockwise quarter turns stored
        # in power). The nth move is stored in position n-1
        self.axis = [0] * self.max_length
        self.power = [0] * self.max_length

        # the lists twist, flip and udslice store the phase 1 coordinates after
        # n moves. position 0 stores the inital states, the coordinates after n
        # moves are stored in position n
        self.twist = [0] * self.max_length
        self.flip = [0] * self.max_length
        self.udslice = [0] * self.max_length

        # similarly to above, these lists store the phase 2 coordinates after n
        # moves.
        self.corner = [0] * self.max_length
        self.edge4 = [0] * self.max_length
        self.edge8 = [0] * self.max_length

        # the following two arrays store minimum number of moves required to
        # reach phase 2 or a solution respectively
        # after n moves. these estimates come from the pruning tables and are
        # used to exclude branches in the search tree.
        self.min_dist_1 = [0] * self.max_length
        self.min_dist_2 = [0] * self.max_length

        # initialise the arrays from the input
        self.f = FaceCube(self.facelets)
        self.c = CoordCube.from_cubiecube(self.f.to_cubiecube())
        self.twist[0] = self.c.twist
        self.flip[0] = self.c.flip
        self.udslice[0] = self.c.udslice
        self.corner[0] = self.c.corner
        self.edge4[0] = self.c.edge4
        self.edge8[0] = self.c.edge8
        self.min_dist_1[0] = self._phase_1_cost(0)

    def _phase_2_initialise(self, n):
        if time.time() - self.t_start > self.timeout:
            return -2
        # initialise phase 2 search from the phase 1 solution
        cc = self.f.to_cubiecube()
        for i in range(n):
            for j in range(self.power[i]):
                cc.multiply(MOVE_CUBE[self.axis[i]])
        self.edge4[n] = cc.edge4
        self.edge8[n] = cc.edge8
        self.corner[n] = cc.corner
        self.min_dist_2[n] = self._phase_2_cost(n)
        for depth in range(self._allowed_length - n):
            m = self._phase_2_search(n, depth)
            if m >= 0:
                return m
        return -1

    def _phase_1_cost(self, n):
        """
        Cost of current position for use in phase 1. Returns a lower bound on
        the number of moves requires to get to phase 2.
        """
        udslice_twist = self.udslice[n] * TWIST + self.twist[n]
        udslice_flip = self.udslice[n] * FLIP + self.flip[n]
        return max(
            CoordCube.tables["udslice_twist_prune"][udslice_twist],
            CoordCube.tables["udslice_flip_prune"][udslice_flip],
        )

    def _phase_2_cost(self, n):
        """
        Cost of current position for use in phase 2. Returns a lower bound on
        the number of moves required to get to a solved cube.
        """
        edge4_corner = self.edge4[n] * CORNER + self.corner[n]
        edge4_edge8 = self.edge4[n] * EDGE8 + self.edge8[n]
        return max(
            CoordCube.tables["edge4_corner_prune"][edge4_corner],
            CoordCube.tables["edge4_edge8_prune"][edge4_edge8],
        )

    def _phase_1_search(self, n, depth):
        if time.time() - self.t_start > self.timeout:
            return -2
        elif self.min_dist_1[n] == 0:
            return self._phase_2_initialise(n)
        elif self.min_dist_1[n] <= depth:
            for i in range(6):
                if n > 0 and self.axis[n - 1] in (i, i + 3):
                    # don't turn the same face on consecutive moves
                    # also for opposite faces, e.g. U and D, UD = DU, so we can
                    # assume that the lower index happens first.
                    continue
                for j in range(1, 4):
                    self.axis[n] = i
                    self.power[n] = j
                    mv = 3 * i + j - 1

                    # update coordinates
                    self.twist[n + 1] = CoordCube.tables["twist_move"][
                        self.twist[n]
                    ][mv]
                    self.flip[n + 1] = CoordCube.tables["flip_move"][
                        self.flip[n]
                    ][mv]
                    self.udslice[n + 1] = CoordCube.tables["udslice_move"][
                        self.udslice[n]
                    ][mv]
                    self.min_dist_1[n + 1] = self._phase_1_cost(n + 1)

                    # start search from next node
                    m = self._phase_1_search(n + 1, depth - 1)
                    if m >= 0:
                        return m
                    if m == -2:
                        return -2
        # if no solution found at current depth, return -1
        return -1

    def _phase_2_search(self, n, depth):
        if self.min_dist_2[n] == 0:
            print("Solution found!")
            return n
        elif self.min_dist_2[n] <= depth:
            for i in range(6):
                if n > 0 and self.axis[n - 1] in (i, i + 3):
                    continue
                for j in range(1, 4):
                    if i in [1, 2, 4, 5] and j != 2:
                        # in phase two we only allow half turns of the faces
                        # R, F, L, B
                        continue
                    self.axis[n] = i
                    self.power[n] = j
                    mv = 3 * i + j - 1

                    # update coordinates following the move mv
                    self.edge4[n + 1] = CoordCube.tables["edge4_move"][
                        self.edge4[n]
                    ][mv]
                    self.edge8[n + 1] = CoordCube.tables["edge8_move"][
                        self.edge8[n]
                    ][mv]
                    self.corner[n + 1] = CoordCube.tables["corner_move"][
                        self.corner[n]
                    ][mv]
                    self.min_dist_2[n + 1] = self._phase_2_cost(n + 1)

                    # start search from new node
                    m = self._phase_2_search(n + 1, depth - 1)
                    if m >= 0:
                        return m
        # if no moves lead to a tree with a solution or min_dist_2 > depth then
        # we return -1 to signify lack of solution
        return -1

    def _solution_to_string(self, length):
        """
        Generate solution string. Uses standard cube notation: F means
        clockwise quarter turn of the F face, U' means a counter clockwise
        quarter turn of the U face, R2 means a half turn of the R face etc.
        """
        s = ""
        for i in range(length):
            s += color.COLORS[self.axis[i]]
            if self.power[i] == 1:
                s += " "
            elif self.power[i] == 2:
                s += "2 "
            elif self.power[i] == 3:
                s += "' "
        return s
