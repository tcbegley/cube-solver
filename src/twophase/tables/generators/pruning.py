from __future__ import annotations

import array
from collections import deque

from tqdm.auto import tqdm

from twophase.constants import (
    CORNER_CLASSES,
    CORNER_MAX,
    EDGE4_MAX,
    EDGE8_MAX,
    FLIP_MAX,
    FLIP_UD_SLICE_CLASSES,
    MOVES,
    PHASE_1_MOVES,
    PHASE_2_MOVES,
    SYMMETRIES_D4H,
    TWIST_MAX,
)
from twophase.tables._array import BitpackedArray, dtypes
from twophase.tables.cubiecube import CubieCube
from twophase.tables.symmetries import Symmetries


def _get_coord_preserving_symmetries(
    name: str, n_classes: int, class_representative_lookup: array.array, edge: bool
) -> array.array:
    # this table tracks which symmetries preserve the flip_ud_slice coordinate for each
    # equivalence class. use a sixteen bit binary number where each bit acts as a flag
    # for the ith symmetry
    coord_preserving_symmetries = array.array(dtypes.u16, [0] * n_classes)
    symmetries = Symmetries(subgroup=True)
    cube = CubieCube()

    for class_idx in range(n_classes):
        coord = class_representative_lookup[class_idx]
        setattr(cube, name, coord)
        for s, symmetry in enumerate(symmetries):
            if edge:
                conj_cube = symmetry.edge_multiply(
                    cube.edge_multiply(symmetries.inverse[s])
                )
            else:
                conj_cube = symmetry.corner_multiply(
                    cube.corner_multiply(symmetries.inverse[s])
                )
            if getattr(conj_cube, name) == coord:
                coord_preserving_symmetries[class_idx] |= 1 << s

    return coord_preserving_symmetries


def _forward_search(
    table: BitpackedArray,
    pbar: tqdm,
    coord1_move: array.array | FlipUDSliceMoveTable,
    coord2_move: array.array,
    coord1_class_lookup: array.array,
    coord1_symmetry_lookup: array.array,
    coord1_representative_lookup: array.array,
    coord2_conj: array.array,
    coord2_max: int,
    coord_preserving_symmetries: array.array,
    max_depth: int,
    phase_2: bool = False,
) -> int:
    moves_iter = PHASE_2_MOVES if phase_2 else PHASE_1_MOVES
    table[0] = 0
    count = 1
    queue = deque([(0, 0)])

    while queue:
        coord1_class_coord2, depth = queue.popleft()

        coord1_class, coord2 = divmod(coord1_class_coord2, coord2_max)
        coord1 = coord1_representative_lookup[coord1_class]

        for mv in moves_iter:
            coord11 = coord1_move[MOVES * coord1 + mv]
            coord1_class1 = coord1_class_lookup[coord11]
            coord1_sym1 = coord1_symmetry_lookup[coord11]
            coord21 = coord2_conj[
                SYMMETRIES_D4H * coord2_move[MOVES * coord2 + mv] + coord1_sym1
            ]
            coord1_class_coord21 = coord2_max * coord1_class1 + coord21

            if table[coord1_class_coord21] == 0b11:
                table[coord1_class_coord21] = (depth + 1) % 3
                if depth < max_depth:
                    queue.append((coord1_class_coord21, depth + 1))
                count += 1
                pbar.update(1)

                sym = coord_preserving_symmetries[coord1_class1]
                if sym == 1:
                    continue

                for k in range(1, 16):
                    sym >>= 1
                    if sym % 2 == 1:
                        coord22 = coord2_conj[SYMMETRIES_D4H * coord21 + k]
                        coord1_class_coord22 = coord2_max * coord1_class1 + coord22
                        if table[coord1_class_coord22] == 0b11:
                            table[coord1_class_coord22] = (depth + 1) % 3
                            if depth < max_depth:
                                queue.append((coord1_class_coord22, depth + 1))
                            count += 1
                            pbar.update(1)

    return count


def _backward_search(
    table: BitpackedArray,
    pbar: tqdm,
    coord1_move: array.array | FlipUDSliceMoveTable,
    coord2_move: array.array,
    coord1_class_lookup: array.array,
    coord1_symmetry_lookup: array.array,
    coord1_representative_lookup: array.array,
    coord2_conj: array.array,
    coord2_max: int,
    depth: int,
    count: int,
    total: int,
) -> None:
    while count < total:
        depth3 = depth % 3
        for coord1_class_coord2 in range(total):
            if table[coord1_class_coord2] != 0b11:
                continue

            coord1_class, coord2 = divmod(coord1_class_coord2, coord2_max)
            coord1 = coord1_representative_lookup[coord1_class]

            for mv in PHASE_1_MOVES:
                coord11 = coord1_move[MOVES * coord1 + mv]
                coord1_class1 = coord1_class_lookup[coord11]
                coord1_sym1 = coord1_symmetry_lookup[coord11]
                coord21 = coord2_conj[
                    SYMMETRIES_D4H * coord2_move[MOVES * coord2 + mv] + coord1_sym1
                ]
                coord1_class_coord21 = coord2_max * coord1_class1 + coord21

                if table[coord1_class_coord21] == depth3:
                    table[coord1_class_coord2] = (depth + 1) % 3
                    pbar.update(1)
                    count += 1
                    break
        depth += 1


class FlipUDSliceMoveTable:
    """
    Mimics a flip_ud_slice_move table without actually computing all the entries.
    """

    def __init__(self, flip_move, ud_slice_sorted_move):
        self.flip_move = flip_move
        self.ud_slice_sorted_move = ud_slice_sorted_move

    def __getitem__(self, flip_ud_slice_move):
        flip_ud_slice, move = divmod(flip_ud_slice_move, MOVES)
        ud_slice, flip = divmod(flip_ud_slice, FLIP_MAX)
        flip_new = self.flip_move[MOVES * flip + move]
        ud_slice_new = (
            self.ud_slice_sorted_move[MOVES * EDGE4_MAX * ud_slice + move] // EDGE4_MAX
        )
        return FLIP_MAX * ud_slice_new + flip_new


def make_flip_ud_slice_class_twist_prune_table(
    twist_move: array.array,
    flip_move: array.array,
    ud_slice_sorted_move: array.array,
    flip_ud_slice_class_lookup: array.array,
    flip_ud_slice_symmetry_lookup: array.array,
    flip_ud_slice_representative_lookup: array.array,
    twist_conj: array.array,
) -> BitpackedArray:
    total = FLIP_UD_SLICE_CLASSES * TWIST_MAX
    table = BitpackedArray(total)

    # this table tracks which symmetries preserve the flip_ud_slice coordinate for each
    # equivalence class
    coord_preserving_symmetries = _get_coord_preserving_symmetries(
        "flip_ud_slice",
        FLIP_UD_SLICE_CLASSES,
        flip_ud_slice_representative_lookup,
        edge=True,
    )

    pbar = tqdm(total=total, desc="flip_ud_slice_class_twist prune table")
    flip_ud_slice_move = FlipUDSliceMoveTable(flip_move, ud_slice_sorted_move)

    # forward search
    count = _forward_search(
        table=table,
        pbar=pbar,
        coord1_move=flip_ud_slice_move,
        coord2_move=twist_move,
        coord1_class_lookup=flip_ud_slice_class_lookup,
        coord1_symmetry_lookup=flip_ud_slice_symmetry_lookup,
        coord1_representative_lookup=flip_ud_slice_representative_lookup,
        coord2_conj=twist_conj,
        coord2_max=TWIST_MAX,
        coord_preserving_symmetries=coord_preserving_symmetries,
        max_depth=8,
    )

    # backward search
    _backward_search(
        table=table,
        pbar=pbar,
        coord1_move=flip_ud_slice_move,
        coord2_move=twist_move,
        coord1_class_lookup=flip_ud_slice_class_lookup,
        coord1_symmetry_lookup=flip_ud_slice_symmetry_lookup,
        coord1_representative_lookup=flip_ud_slice_representative_lookup,
        coord2_conj=twist_conj,
        coord2_max=TWIST_MAX,
        depth=9,
        count=count,
        total=total,
    )

    return table


def make_corner_class_edge8_prune_table(
    corner_move: array.array,
    edge8_move: array.array,
    corner_class_lookup: array.array,
    corner_symmetry_lookup: array.array,
    corner_representative_lookup: array.array,
    edge8_conj: array.array,
    max_depth: int = 9,
) -> BitpackedArray:
    total = CORNER_CLASSES * EDGE8_MAX
    table = BitpackedArray(total)

    coord_preserving_symmetries = _get_coord_preserving_symmetries(
        "corner", CORNER_CLASSES, corner_representative_lookup, edge=False
    )
    pbar = tqdm(total=total, desc="corner_class_edge8 prune table")

    _forward_search(
        table,
        pbar,
        corner_move,
        edge8_move,
        corner_class_lookup,
        corner_symmetry_lookup,
        corner_representative_lookup,
        edge8_conj,
        EDGE8_MAX,
        coord_preserving_symmetries,
        max_depth,
        phase_2=True,
    )

    return table


def make_cornslice_prune_table(
    corner_move: array.array, ud_slice_sorted_move: array.array
) -> array.array:
    """
    Pruning table storing exact depths for (corner, edge4) coordinate pairs using
    phase 2 moves. Used as an additional pruning check during phase 2 search.

    Unlike the other pruning tables this stores exact depths (not mod 3)
    in a regular array, since the coordinate space is small enough
    (CORNER_MAX * EDGE4_MAX = 967,680).
    """
    total = CORNER_MAX * EDGE4_MAX
    table = array.array(dtypes.u16, [0xFFFF] * total)
    table[0] = 0

    done = 1
    depth = 0
    pbar = tqdm(total=total, desc="cornslice prune table")
    pbar.update(1)

    while done < total:
        for corner in range(CORNER_MAX):
            for edge4 in range(EDGE4_MAX):
                idx = EDGE4_MAX * corner + edge4
                if table[idx] != depth:
                    continue
                for mv in PHASE_2_MOVES:
                    corner1 = corner_move[MOVES * corner + mv]
                    edge4_1 = ud_slice_sorted_move[MOVES * edge4 + mv]
                    idx1 = EDGE4_MAX * corner1 + edge4_1
                    if table[idx1] == 0xFFFF:
                        table[idx1] = depth + 1
                        done += 1
                        pbar.update(1)
        depth += 1

    return table
