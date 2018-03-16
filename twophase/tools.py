# Module for helpful miscellaneous shizzle
import random

from . import color, coord_cube, cubie_cube, face_cube


# Verify string input
def verify(s):
    count = [0]*6
    try:
        for char in s:
            count[color.COLORS[char]] += 1
    except (IndexError, ValueError):
        return -1
    for i in range(6):
        if count[i] != 9:
            return -1

    fc = face_cube.FaceCube(s)
    cc = fc.to_cubiecube()

    return cc.verify()


def random_cube():
    cc = cubie_cube.CubieCube()
    cc.set_flip(random.randint(0, coord_cube.flip))
    cc.set_twist(random.randint(0, coord_cube.twist))
    while True:
        cc.set_corner(random.randint(0, coord_cube.corner))
        cc.set_edge(random.randint(0, coord_cube.edge))
        if cc.edge_parity() == cc.corner_parity():
            break
    fc = cc.to_facecube()
    return fc.to_string()
