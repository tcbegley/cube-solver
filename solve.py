import time

import color
import tools
from coord_cube import CORNER, EDGE8, FLIP, TWIST, CoordCube
from cubie_cube import MOVE_CUBE
from face_cube import FaceCube


class Solver:
    def __init__(
        self,
        facelets="UUUUUUUUURRRRRRRRRFFFFFFFFFDDDDDDDDDLLLLLLLLLBBBBBBBBB",
        max_length=25
    ):
        # store facelet representation and max solution length
        self.facelets = facelets
        self.max_length = max_length

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
        self.f = FaceCube(facelets)
        self.c = CoordCube(self.f.to_cubiecube())
        self.twist[0] = self.c.twist
        self.flip[0] = self.c.flip
        self.udslice[0] = self.c.udslice
        self.corner[0] = self.c.corner
        self.edge4[0] = self.c.edge4
        self.edge8[0] = self.c.edge8
        self.min_dist_1[0] = self.phase_1_cost(0)

    def solution_to_string(self, length):
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

    def phase_1_cost(self, n):
        """
        Cost of current position for use in phase 1. Returns a lower bound on
        the number of moves requires to get to phase 2.
        """
        slice_twist = self.udslice[n] * TWIST + self.twist[n]
        slice_flip = self.udslice[n] * FLIP + self.flip[n]
        return max(
            CoordCube.tables['slice_twist_prun'][slice_twist],
            CoordCube.tables['slice_flip_prun'][slice_flip]
        )

    def phase_2_cost(self, n):
        """
        Cost of current position for use in phase 2. Returns a lower bound on
        the number of moves required to get to a solved cube.
        """
        edge4_corner = self.edge4[n] * CORNER + self.corner[n]
        edge4_edge8 = self.edge4[n] * EDGE8 + self.edge8[n]
        return max(
            CoordCube.tables['edge4_corner_prun'][edge4_corner],
            CoordCube.tables['edge4_edge8_prun'][edge4_edge8]
        )

    def solve(self, timeout=10):
        """
        Solve the cube.

        This method implements back to back IDA* searches for phase 1 and phase
        2. Once the first solution has been found the algorithm checks for
        shorter solutions, including checking whether there is a shorter
        overall solution with a longer first phase.
        """
        if tools.verify(self.facelets):
            return "Error: {}".format(tools.verify(self.facelets))

        self.timeout = timeout
        self.t_start = time.time()

        while time.time() - self.t_start <= self.timeout:
            solution_found = False
            for depth in range(self.max_length):
                n = self.phase_1_search(0, depth)
                if n >= 0:
                    solution_found = True
                    print(self.solution_to_string(n))
                    self.max_length = n - 1
                    break
                if n == -2:
                    return "Error: Timeout"
            if not solution_found:
                return "No shorter solution found."
        return "Error: Timeout"

    def phase_1_search(self, n, depth):
        if time.time() - self.t_start > self.timeout:
            # Timeout
            return -2
        if self.min_dist_1[n] == 0:
            # print("Finished phase 1! Starting phase 2.")
            return self.phase_2_start(n)
        elif self.min_dist_1[n] <= depth:
            for i in range(6):
                if (n > 0 and
                        (self.axis[n - 1] == i or self.axis[n - 1] == i + 3)):
                    # don't turn the same face on consecutive moves
                    # also for opposite faces, e.g. U and D, UD = DU, so we can
                    # assume that the lower index happens first.
                    continue
                for j in range(1, 4):
                    self.axis[n] = i
                    self.power[n] = j
                    mv = 3 * i + j - 1

                    # update coordinates
                    self.twist[n+1] = (
                        CoordCube.tables['twist_move'][self.twist[n]][mv]
                    )
                    self.flip[n+1] = (
                        CoordCube.tables['flip_move'][self.flip[n]][mv]
                    )
                    self.udslice[n+1] = (
                        CoordCube.tables['slice_move'][self.udslice[n]][mv]
                    )
                    self.min_dist_1[n+1] = (
                        self.phase_1_cost(n+1)
                    )

                    # start search from next node
                    m = self.phase_1_search(n + 1, depth - 1)
                    if m >= 0:
                        return m
                    if m == -2:
                        # Timeout
                        return -2
        # if no solution found at current depth, return -1
        return -1

    def phase_2_start(self, n):
        if time.time() - self.t_start > self.timeout:
            # Timeout
            return -2
        # initialise phase 2 search from the phase 1 solution
        cc = self.f.to_cubiecube()
        for i in range(n):
            for j in range(self.power[i]):
                cc.multiply(MOVE_CUBE[self.axis[i]])
        self.edge4[n] = cc.edge4
        self.edge8[n] = cc.edge8
        self.corner[n] = cc.corner
        self.min_dist_2[n] = self.phase_2_cost(n)
        for depth in range(self.max_length - n):
            # print("Phase 2: Searching at depth " + repr(depth))
            m = self.phase_2_search(n, depth)
            if m >= 0:
                return m
        # print("Phase 2: I didn't find anything...")
        return -1

    def phase_2_search(self, n, depth):
        # print("Phase 2 search: n = " + repr(n) + ", depth = " + repr(depth))
        if self.min_dist_2[n] == 0:
            print("Solution found!")
            return n
        elif self.min_dist_2[n] <= depth:
            for i in range(6):
                if (n > 0 and
                        (self.axis[n - 1] == i or self.axis[n - 1] == i + 3)):
                    # don't repeat face turns
                    continue
                for j in range(1, 4):
                    if i in [1, 2, 4, 5] and j != 2:
                        # in phase two we only allow half turns of the faces
                        # R, F, L, B
                        continue
                    self.axis[n] = i
                    self.power[n] = j
                    mv = 3*i + j - 1

                    # update coordinates following the move mv
                    self.edge4[n+1] = (
                        CoordCube.tables['edge4_move'][self.edge4[n]][mv]
                    )
                    self.edge8[n+1] = (
                        CoordCube.tables['edge8_move'][self.edge8[n]][mv]
                    )
                    self.corner[n+1] = (
                        CoordCube.tables['corner_move'][self.corner[n]][mv]
                    )
                    self.min_dist_2[n+1] = self.phase_2_cost(n+1)

                    # start search from new node
                    m = self.phase_2_search(n+1, depth-1)
                    if m >= 0:
                        return m
        # if no moves lead to a tree with a solution or min_dist_2 > depth then
        # we return -1 to signify lack of solution
        return -1
