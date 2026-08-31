import array

from tqdm import trange

from twophase.constants import EDGE4_MAX, EDGE8_MAX
from twophase.tables._array import dtypes, max_val_to_dtype
from twophase.tables.cubiecube import CubieCube


def make_edge_merge_table() -> array.array:
    """
    The edge_merge table is used in phase 2 to map (u_edges_sorted, d_edges_sorted) to
    edge8. This is possible because in phase 2 the u edges and d edges are necessarily
    in the u and d layers.
    """
    dtype = max_val_to_dtype(EDGE8_MAX)
    table = array.array(dtype, [0] * EDGE8_MAX)

    cube = CubieCube()
    for i in trange(EDGE8_MAX, desc="edge_merge table"):
        cube.edge8 = i
        table[EDGE4_MAX * cube.u_edges_sorted + cube.d_edges_sorted % EDGE4_MAX] = i

    return table


def make_depth_lookup_table() -> array.array:
    """
    The depth_lookup table is used during search. The pruning tables only store the
    depth mod 3, so it's convenient to have a fast way to look up the new min depth
    from the old depth + the new depth mod 3. This is possible since depth can only
    change by ±1 (or 0) with each move.
    """
    table = array.array(dtypes.u8, [0] * 20 * 3)

    for depth in range(20):
        for depth3 in range(3):
            if depth % 3 == 0 and depth3 == 2:
                table[3 * depth + depth3] = max(depth - 1, 0)
            elif depth % 3 == 2 and depth3 == 0:
                table[3 * depth + depth3] = depth + 1
            else:
                table[3 * depth + depth3] = depth + (depth3 - depth % 3)

    return table
