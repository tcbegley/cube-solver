import array

from tqdm.auto import tqdm

from twophase.constants import EDGE8_MAX, MOVES, SYMMETRIES, SYMMETRIES_D4H, TWIST_MAX
from twophase.tables._array import dtypes, max_val_to_dtype
from twophase.tables.cubiecube import CubieCube, Moves
from twophase.tables.symmetries import Symmetries


# lookup table for symmetry conjugated moves
def make_move_conj_table() -> array.array:
    symmetries = Symmetries()
    moves = Moves()

    table = array.array(dtypes.u8, [0] * MOVES * SYMMETRIES)
    for i, sym in enumerate(symmetries):
        for j, mv in enumerate(moves):
            conj_mv = sym * mv * symmetries.inverse[i]
            for k, mv2 in enumerate(moves):
                if conj_mv == mv2:
                    table[MOVES * i + j] = k

    return table


def _make_conj_table(name: str, max_val: int, edge: bool) -> array.array:
    table = array.array(max_val_to_dtype(max_val), [0] * SYMMETRIES_D4H * max_val)
    d4h_symmetries = Symmetries(subgroup=True)

    cube = CubieCube()
    pbar = tqdm(total=SYMMETRIES_D4H * max_val, desc=f"{name} conj table")

    for coord in range(max_val):
        setattr(cube, name, coord)
        for s, sym in enumerate(d4h_symmetries):
            if edge:
                conj_cube = sym.edge_multiply(
                    cube.edge_multiply(d4h_symmetries.inverse[s])
                )
            else:
                conj_cube = sym.corner_multiply(
                    cube.corner_multiply(d4h_symmetries.inverse[s])
                )
            table[SYMMETRIES_D4H * coord + s] = getattr(conj_cube, name)
        pbar.update(SYMMETRIES_D4H)
    return table


def make_twist_conj_table() -> array.array:
    return _make_conj_table("twist", TWIST_MAX, edge=False)


def make_edge8_conj_table() -> array.array:
    return _make_conj_table("edge8", EDGE8_MAX, edge=True)
