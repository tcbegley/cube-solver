import random

from .cubes import cubiecube
from .tables import Tables


def random_cube():
    cc = cubiecube.CubieCube()
    cc.flip = random.randint(0, Tables.FLIP)
    cc.twist = random.randint(0, Tables.TWIST)
    while True:
        cc.corner = random.randint(0, Tables.CORNER)
        cc.edge = random.randint(0, Tables.EDGE)
        if cc.edge_parity == cc.corner_parity:
            break
    fc = cc.to_facecube()
    return fc.to_string()
