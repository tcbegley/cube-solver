import Color
import Tools
import CoordCube
import CubieCube
import FaceCube
import time


class Solver:
    def __init__(
        self,
        facelets="UUUUUUUUURRRRRRRRRFFFFFFFFFDDDDDDDDDLLLLLLLLLBBBBBBBBB",
        max_length=25
    ):
        # store facelet representation and max solution length
        self.facelets = facelets
        self.max_length = max_length

        # the lists 'axis' and 'power' will store the nth move (index of face being turned stored in axis, number
        # of clockwise quarter turns stored in power). The nth move is stored in position n-1
        self.axis = [0] * 31
        self.power = [0] * 31

        # the lists twist, flip and udslice store the phase 1 coordinates after n moves. position 0 stores the inital
        # states, the coordinates after n moves are stored in position n
        self.twist = [0] * 31
        self.flip = [0] * 31
        self.udslice = [0] * 31

        # similarly to above, these lists store the phase 2 coordinates after n moves.
        self.corner = [0] * 31
        self.edge4 = [0] * 31
        self.edge8 = [0] * 31

        # the following two arrays store minimum number of moves required to reach phase 2 or a solution respectively
        # after n moves. these estimates come from the pruning tables and are used to exclude branches in the search
        # tree.
        self.min_dist_1 = [0] * 31
        self.min_dist_2 = [0] * 31

        # upper bound on the number of moves a solution is allowed to have
        self.max_length = 30

        # upper bound on time spent searching solution
        self.timeout = 10

        # initialise the arrays from the input
        self.f = FaceCube.FaceCube(facelets)
        self.c = CoordCube.CoordCube(self.f.to_cubiecube())
        self.twist[0] = self.c.twist
        self.flip[0] = self.c.flip
        self.udslice[0] = self.c.udslice
        self.corner[0] = self.c.corner
        self.edge4[0] = self.c.edge4
        self.edge8[0] = self.c.edge8
        self.min_dist_1[0] = self.phase_1_cost(0)

    def solution_to_string(self, length):
        # given an instance of solver and the length of the solution, this loops through axis and power and outputs the
        # solution as a string
        s = ""
        for i in range(length):
            s += Color.c[self.axis[i]]
            if self.power[i] == 1:
                s += " "
            elif self.power[i] == 2:
                s += "2 "
            elif self.power[i] == 3:
                s += "' "
        return s

    def phase_1_cost(self, n):
        # lower bound for number of moves needed to get to phase 2.
        return max(CoordCube.slice_twist_prun[self.udslice[n] * CoordCube.twist + self.twist[n]],
                   CoordCube.slice_flip_prun[self.udslice[n] * CoordCube.flip + self.flip[n]])

    def phase_2_cost(self, n):
        # lower bound for number of moves needed to get to clean cube.
        return max(CoordCube.edge4_corner_prun[self.edge4[n] * CoordCube.corner + self.corner[n]],
                   CoordCube.edge4_edge8_prun[self.edge4[n] * CoordCube.edge8 + self.edge8[n]])

    def solve(self, timeout=10):
        # implements back to back IDA* searches to first get the cube to phase 2, then to a clean cube.
        if Tools.verify(self.facelets):
            return "Error: " + repr(Tools.verify(self.facelets))

        self.timeout = timeout

        # keep track of elapsed time so that we can force a timeout if necessary
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
                if n > 0 and (self.axis[n - 1] == i or self.axis[n - 1] == i + 3):
                    # don't turn the same face on consecutive moves
                    # also for opposite faces, e.g. U and D, UD = DU, so we can
                    # assume that the lower index happens first.
                    continue
                for j in range(1, 4):
                    self.axis[n] = i
                    self.power[n] = j
                    mv = 3 * i + j - 1

                    # update coordinates
                    self.twist[n + 1] = CoordCube.twist_move[self.twist[n]][mv]
                    self.flip[n + 1] = CoordCube.flip_move[self.flip[n]][mv]
                    self.udslice[n +
                                 1] = CoordCube.slice_move[self.udslice[n]][mv]
                    self.min_dist_1[n + 1] = self.phase_1_cost(n + 1)

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
                cc.multiply(CubieCube.move_cube[self.axis[i]])
        self.edge4[n] = cc.get_edge4()
        self.edge8[n] = cc.get_edge8()
        self.corner[n] = cc.get_corner()
        self.min_dist_2[n] = self.phase_2_cost(n)
        for depth in range(self.max_length - n):
            # print("Phase 2: Searching at depth " + repr(depth))
            m = self.phase_2_search(n, depth)
            if m >= 0:
                return m
        #print("Phase 2: I didn't find anything...")
        return -1

    def phase_2_search(self, n, depth):
        # print("Phase 2 search: n = " + repr(n) + ", depth = " + repr(depth))
        if self.min_dist_2[n] == 0:
            print("Solution found!")
            return n
        elif self.min_dist_2[n] <= depth:
            for i in range(6):
                if n > 0 and (self.axis[n - 1] == i or self.axis[n - 1] == i + 3):
                    # don't repeat face turns
                    continue
                for j in range(1, 4):
                    if i in [1, 2, 4, 5] and j != 2:
                        # in phase two we only allow half turns of the faces R, F, L, B
                        continue
                    self.axis[n] = i
                    self.power[n] = j
                    mv = 3 * i + j - 1

                    # update coordinates following the move mv
                    self.edge4[n + 1] = CoordCube.edge4_move[self.edge4[n]][mv]
                    self.edge8[n + 1] = CoordCube.edge8_move[self.edge8[n]][mv]
                    self.corner[n +
                                1] = CoordCube.corner_move[self.corner[n]][mv]
                    self.min_dist_2[n + 1] = self.phase_2_cost(n + 1)

                    # start search from new node
                    m = self.phase_2_search(n + 1, depth - 1)
                    if m >= 0:
                        return m
        # if no moves lead to a tree with a solution or min_dist_2 > depth then we return -1 to signify lack of soln
        return -1
