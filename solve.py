import time

import color
import coord_cube
import cubie_cube
import face_cube
import tools


def solution_to_string(axis, power):
    # Given axis and power arrays, converts moves to solution string
    s = ""
    for a, p in zip(axis, power):
        s += Color.c[a]
        if p == 1:
            s += " "
        elif p == 2:
            s += "2 "
        elif p == 3:
            s += "' "
    return s


def phase_1_cost(tw, fl, uds):
    # lower bound for number of moves needed to get to phase 2.
    return max(CoordCube.slice_twist_prun[uds * CoordCube.twist + tw],
               CoordCube.slice_flip_prun[uds * CoordCube.flip + fl])


def phase_2_cost(e4, e8, co):
    # lower bound for number of moves needed to solve cube in phase 2
    return max(
        CoordCube.edge4_edge8_prun[e4 * CoordCube.edge8 + e8],
        CoordCube.edge4_corner_prun[e4 * CoordCube.corner + co])


def solve(
    facelets="UUUUUUUUURRRRRRRRRFFFFFFFFFDDDDDDDDDLLLLLLLLLBBBBBBBBB",
    max_length=25,
    timeout=10
):
    # implements back to back IDA* searches to first get the cube to phase 2,
    # then to a clean cube.
    if tools.verify(facelets):
        return "Error: " + repr(Tools.verify(facelets))

    t_start = time.time()

    while time.time() - t_start <= timeout:
            solution_found = False
            for depth in range(self.max_length):
                n = self.phase_1_search(0, depth)
                if n >= 0:
                    solution_found = True
                    print(solution_to_string(n))
                    self.max_length = n - 1
                    break
                if n == -2:
                    return "Error: Timeout"
            if not solution_found:
                return "No shorter solution found."
    return "Error: Timeout"
