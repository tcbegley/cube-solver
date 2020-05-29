import random

from . import coord_cube, cubie_cube


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
