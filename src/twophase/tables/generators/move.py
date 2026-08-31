import array

from tqdm import tqdm

from twophase import constants
from twophase.tables._array import max_val_to_dtype
from twophase.tables.cubiecube import CubieCube, move


def _make_move_table(
    name: str, max_val: int, edge: bool, phase2: bool = False
) -> array.array:
    dtype = max_val_to_dtype(max_val)
    table = array.array(dtype, [0] * constants.MOVES * max_val)
    cube = CubieCube()
    pbar = tqdm(total=constants.MOVES * max_val, desc=f"{name} table")
    for i in range(max_val):
        setattr(cube, name, i)
        for mv in range(6):
            for rot in range(3):
                cube = move(cube, mv, corner=not edge, edge=edge)
                if phase2 and mv % 3 != 0 and rot % 2 == 0:
                    # in phase 2, only 180 degree turns of the faces R F L B are valid
                    # for some coordinates used in phase 2, making a different turn is
                    # non-sensical, so we skip and leave the entries as 0
                    continue
                table[constants.MOVES * i + 3 * mv + rot] = getattr(cube, name)
            cube = move(cube, mv, corner=not edge, edge=edge)
        pbar.update(constants.MOVES)
    return table


# used in phase 1
def make_twist_move_table() -> array.array:
    return _make_move_table("twist", constants.TWIST_MAX, edge=False)


# phase 1
def make_flip_move_table() -> array.array:
    return _make_move_table("flip", constants.FLIP_MAX, edge=True)


# phase 1 and phase 2
def make_ud_slice_sorted_move_table() -> array.array:
    return _make_move_table(
        "ud_slice_sorted", constants.UD_SLICE_MAX * constants.EDGE4_MAX, edge=True
    )


# phase 1 -> 2 transition
def make_u_edges_sorted_move_table() -> array.array:
    return _make_move_table(
        "u_edges_sorted", constants.UD_SLICE_MAX * constants.EDGE4_MAX, edge=True
    )


# phase 1 -> 2 transition
def make_d_edges_sorted_move_table() -> array.array:
    return _make_move_table(
        "d_edges_sorted", constants.UD_SLICE_MAX * constants.EDGE4_MAX, edge=True
    )


# phase 2
def make_edge8_move_table() -> array.array:
    return _make_move_table("edge8", constants.EDGE8_MAX, edge=True, phase2=True)


# phase 2
def make_corner_move_table() -> array.array:
    return _make_move_table("corner", constants.CORNER_MAX, edge=False)
