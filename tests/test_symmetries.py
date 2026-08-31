import pytest

from twophase.tables.cubiecube import (
    SOLVED_CO,
    SOLVED_CP,
    SOLVED_EO,
    SOLVED_EP,
    CubieCube,
)
from twophase.tables.symmetries import Symmetries, cube_symmetries


def test_symmetries():
    s = Symmetries()

    assert hasattr(s, "_symmetries")
    assert len(s._symmetries) == len(s) == 48
    assert hasattr(s, "_inverse_symmetries")
    assert len(s._inverse_symmetries) == len(s)


def test_inverse_symmetries():
    symmetries = Symmetries()

    for i, sym in enumerate(symmetries):
        cube = sym * symmetries.inverse[i]
        assert (
            cube.co == SOLVED_CO
            and cube.cp == SOLVED_CP
            and cube.eo == SOLVED_EO
            and cube.ep == SOLVED_EP
        )


@pytest.mark.parametrize(
    ["cp", "co", "ep", "eo", "symmetries"],
    [
        (range(8), (0,) * 8, range(12), (0,) * 12, set(range(96))),
        (
            (4, 7, 3, 5, 6, 2, 1, 0),
            (0, 0, 1, 1, 1, 2, 0, 1),
            (0, 1, 6, 2, 3, 5, 4, 7, 8, 9, 10, 11),
            (0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 1, 1),
            {0},
        ),
        (
            range(8),
            (0,) * 8,
            (4, 5, 2, 3, 6, 7, 0, 1, 9, 10, 8, 11),
            (0,) * 12,
            {0, 74},
        ),
    ],
)
def test_cube_symmetries(cp, co, ep, eo, symmetries):
    c = CubieCube(
        cp=tuple(SOLVED_CP[i] for i in cp),
        co=co,
        ep=tuple(SOLVED_EP[i] for i in ep),
        eo=eo,
    )

    syms = cube_symmetries(c)
    assert isinstance(syms, list)
    assert set(syms) == symmetries
