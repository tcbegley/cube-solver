from itertools import chain
from math import comb

import pytest

from twophase.pieces import Corner, Edge
from twophase.tables.cubiecube import (
    _MOVES,
    SOLVED_CP,
    SOLVED_EP,
    CubieCube,
    InvalidCube,
    move,
    verify,
)


@pytest.mark.parametrize(
    "twist,co",
    [
        [0, (0,) * 8],
        [24, (0, 0, 0, 0, 2, 2, 0, 2)],
        [1_234, (1, 2, 0, 0, 2, 0, 1, 0)],
        [1_093, (1, 1, 1, 1, 1, 1, 1, 2)],
    ],
)
def test_twist(twist, co):
    cube = CubieCube(co=co)
    assert cube.twist == twist

    cube = CubieCube()
    cube.twist = twist
    assert cube.co == co


@pytest.mark.parametrize("twist", [-1_000, -1, 3**7, 1_000_000])
def test_twist_raises(twist):
    cube = CubieCube()

    with pytest.raises(ValueError, match=f"{twist} is out of range for twist"):
        cube.twist = twist


@pytest.mark.parametrize(
    "flip,eo",
    [
        [0, (0,) * 12],
        [1_735, (1, 1, 0, 1, 1, 0, 0, 0, 1, 1, 1, 1)],
        [2_016, (1,) * 6 + (0,) * 6],
        [2_047, (1,) * 12],
    ],
)
def test_flip(flip, eo):
    cube = CubieCube(eo=eo)
    assert cube.flip == flip

    cube = CubieCube()
    cube.flip = flip
    assert cube.eo == eo


@pytest.mark.parametrize("flip", [-1_000, -1, 2**11, 1_000_000])
def test_flip_raises(flip):
    cube = CubieCube()

    with pytest.raises(ValueError, match=f"{flip} is out of range for flip"):
        cube.flip = flip


@pytest.mark.parametrize(
    "ud_slice_sorted,ep",
    [
        [0, (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11)],
        [123, (0, 1, 2, 3, 4, 5, 10, 6, 7, 8, 9, 11)],
        [4_321, (0, 1, 9, 2, 8, 10, 3, 11, 4, 5, 6, 7)],
        [10_000, (10, 0, 11, 1, 2, 3, 4, 5, 6, 8, 9, 7)],
        [24 * 495 - 1, (11, 10, 9, 8, 0, 1, 2, 3, 4, 5, 6, 7)],
    ],
)
def test_ud_slice_sorted(ud_slice_sorted, ep):
    cube = CubieCube(ep=ep)
    assert cube.ud_slice_sorted == ud_slice_sorted

    cube = CubieCube()
    cube.ud_slice_sorted = ud_slice_sorted
    assert cube.ep == tuple(SOLVED_EP[i] for i in ep)


@pytest.mark.parametrize("ud_slice_sorted", [-1_000, -1, 11_880, 1_000_000])
def test_ud_slice_sorted_raises(ud_slice_sorted):
    cube = CubieCube()

    with pytest.raises(
        ValueError, match=f"{ud_slice_sorted} is out of range for ud_slice_sorted"
    ):
        cube.ud_slice_sorted = ud_slice_sorted


@pytest.mark.parametrize(
    "u_edges_sorted,ep",
    [
        [0, (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11)],
        [123, (2, 0, 1, 4, 5, 3, 6, 7, 8, 9, 10, 11)],
        [4_321, (4, 5, 6, 7, 1, 8, 0, 2, 9, 3, 10, 11)],
        [10_000, (4, 2, 3, 5, 6, 7, 8, 9, 10, 0, 11, 1)],
        [24 * 495 - 1, (4, 5, 6, 7, 8, 9, 10, 11, 3, 2, 1, 0)],
    ],
)
def test_u_edges_sorted(u_edges_sorted, ep):
    cube = CubieCube(ep=ep)
    assert cube.u_edges_sorted == u_edges_sorted

    cube = CubieCube()
    cube.u_edges_sorted = u_edges_sorted
    assert cube.ep == tuple(SOLVED_EP[i] for i in ep)


@pytest.mark.parametrize("u_edges_sorted", [-1_000, -1, 11_880, 1_000_000])
def test_u_edges_sorted_raises(u_edges_sorted):
    cube = CubieCube()

    with pytest.raises(
        ValueError, match=f"{u_edges_sorted} is out of range for u_edges_sorted"
    ):
        cube.u_edges_sorted = u_edges_sorted


@pytest.mark.parametrize(
    "d_edges_sorted,ep",
    [
        [0, (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11)],
        [123, (0, 1, 6, 2, 3, 4, 5, 7, 8, 9, 10, 11)],
        [4_321, (4, 6, 11, 7, 0, 1, 2, 3, 8, 9, 5, 10)],
        [10_000, (10, 11, 0, 1, 2, 4, 5, 3, 6, 8, 7, 9)],
        [24 * 495 - 1, (8, 9, 10, 11, 0, 1, 2, 3, 7, 6, 5, 4)],
    ],
)
def test_d_edges_sorted(d_edges_sorted, ep):
    cube = CubieCube(ep=ep)
    assert cube.d_edges_sorted == d_edges_sorted

    cube = CubieCube()
    cube.d_edges_sorted = d_edges_sorted
    assert cube.ep == tuple(SOLVED_EP[i] for i in ep)


@pytest.mark.parametrize("d_edges_sorted", [-1_000, -1, 11_880, 1_000_000])
def test_d_edges_sorted_raises(d_edges_sorted):
    cube = CubieCube()

    with pytest.raises(
        ValueError, match=f"{d_edges_sorted} is out of range for d_edges_sorted"
    ):
        cube.d_edges_sorted = d_edges_sorted


def test_d_edges_sorted_phase_2():
    cube = CubieCube()

    for d_edges_sorted in range(24 * comb(8, 4)):
        cube.d_edges_sorted = d_edges_sorted
        assert cube.ep[-4:] == SOLVED_EP[-4:]


@pytest.mark.parametrize(
    "edge8,ep",
    [
        [0, tuple(range(8))],
        [1_234, (2, 6, 0, 3, 4, 1, 5, 7)],
        [10_000, (4, 7, 2, 3, 5, 1, 0, 6)],
        [40_319, (7, 6, 5, 4, 3, 2, 1, 0)],
    ],
)
def test_edge8(edge8, ep):
    cube = CubieCube(ep=tuple(SOLVED_EP[i] for i in chain(ep, range(8, 12))))
    assert cube.edge8 == edge8

    cube = CubieCube()
    cube.edge8 = edge8
    assert cube.ep[:8] == tuple(SOLVED_EP[i] for i in ep)


@pytest.mark.parametrize("edge8", [-1_000, -1, 40_320, 1_000_000])
def test_edge8_raises(edge8):
    cube = CubieCube()

    with pytest.raises(ValueError, match=f"{edge8} is out of range for edge8"):
        cube.edge8 = edge8


@pytest.mark.parametrize(
    "ud_slice,locs",
    [
        [0, {8, 9, 10, 11}],
        [42, {4, 7, 8, 11}],
        [123, {3, 4, 5, 8}],
        [494, {0, 1, 2, 3}],
    ],
)
def test_ud_slice(ud_slice, locs):
    ep = []
    slice_idx = 8
    other_idx = 0
    for i in range(12):
        if i in locs:
            ep.append(SOLVED_EP[slice_idx])
            slice_idx += 1
        else:
            ep.append(SOLVED_EP[other_idx])
            other_idx += 1
    cube = CubieCube(ep=tuple(ep))
    print(f"{ep=}")
    assert cube.ud_slice == ud_slice

    cube = CubieCube()
    cube.ud_slice = ud_slice
    assert set(i for i, edge in enumerate(cube.ep) if edge in SOLVED_EP[8:]) == locs


@pytest.mark.parametrize("ud_slice", [-1_000, -1, 495, 1_000_000])
def test_ud_slice_raises(ud_slice):
    cube = CubieCube()

    with pytest.raises(ValueError, match=f"{ud_slice} is out of range for ud_slice"):
        cube.ud_slice = ud_slice


@pytest.mark.parametrize("ud_slice", [0, 1, 42, 123, 360, 494])
@pytest.mark.parametrize("perm", [0, 1, 11, 23])
def test_ud_slice_ud_slice_sorted_consistency(ud_slice, perm):
    cube1 = CubieCube()
    cube2 = CubieCube()

    cube1.ud_slice = ud_slice
    cube2.ud_slice_sorted = 24 * ud_slice + perm

    assert cube2.ud_slice == cube1.ud_slice
    if perm == 0:
        assert cube1.ud_slice_sorted == cube2.ud_slice_sorted


@pytest.mark.parametrize(
    "corner,cp",
    [
        [0, tuple(range(8))],
        [1_234, (2, 6, 0, 3, 4, 1, 5, 7)],
        [10_000, (4, 7, 2, 3, 5, 1, 0, 6)],
        [40_319, (7, 6, 5, 4, 3, 2, 1, 0)],
    ],
)
def test_corner(corner, cp):
    cube = CubieCube(cp=tuple(SOLVED_CP[i] for i in cp))
    assert cube.corner == corner

    cube = CubieCube()
    cube.corner = corner
    assert cube.cp == tuple(SOLVED_CP[i] for i in cp)


@pytest.mark.parametrize("corner", [-1_000, -1, 40_320, 1_000_000])
def test_corner_raises(corner):
    cube = CubieCube()

    with pytest.raises(ValueError, match=f"{corner} is out of range for corner"):
        cube.corner = corner


def test_verify():
    # replace first edge with repeat of last
    ep = SOLVED_EP[-1:] + SOLVED_EP[1:]
    with pytest.raises(InvalidCube, match="<Edge.BR: 11> appears more than once"):
        verify(CubieCube(ep=ep))

    # rplace first corner with repeat of last
    cp = SOLVED_CP[-1:] + SOLVED_CP[1:]
    with pytest.raises(InvalidCube, match="<Corner.DRB: 7> appears more than once"):
        verify(CubieCube(cp=cp))

    eo = (0,) * 11 + (1,)
    with pytest.raises(InvalidCube, match="Flip error: an edge must be flipped"):
        verify(CubieCube(eo=eo))

    co = (0,) * 7 + (1,)
    with pytest.raises(InvalidCube, match="Twist error: a corner must be twisted"):
        verify(CubieCube(co=co))

    # swap first and last corners
    cp = SOLVED_CP[-1:] + SOLVED_CP[1:-1] + SOLVED_CP[:1]
    with pytest.raises(InvalidCube, match="Parity error"):
        verify(CubieCube(cp=cp))


@pytest.mark.parametrize("m", range(6))
def test_move_basic(m):
    cube = move(CubieCube(), m)
    assert cube == _MOVES[m]


def test_move_compound():
    cube = CubieCube()
    for i in range(6):
        cube = move(cube, i)

    assert cube.cp == (
        Corner.URF,
        Corner.UFL,
        Corner.UBR,
        Corner.DFR,
        Corner.DRB,
        Corner.DLF,
        Corner.ULB,
        Corner.DBL,
    )
    assert cube.co == (1, 1, 2, 0, 2, 1, 0, 2)
    assert cube.ep == (
        Edge.FR,
        Edge.FL,
        Edge.BL,
        Edge.UB,
        Edge.DR,
        Edge.DL,
        Edge.DF,
        Edge.DB,
        Edge.UR,
        Edge.UF,
        Edge.UL,
        Edge.BR,
    )
    assert cube.eo == (0, 1, 0, 1, 1, 0, 1, 1, 1, 0, 1, 1)
