import pytest

from twophase import Move, format_moves, parse, solve, solve_progressively
from twophase.exceptions import InvalidCube

SOLVED = "UUUUUUUUURRRRRRRRRFFFFFFFFFDDDDDDDDDLLLLLLLLLBBBBBBBBB"
U_TURN = "UUUUUUUUUBBBRRRRRRRRRFFFFFFDDDDDDDDDFFFLLLLLLLLLBBBBBB"


def test_format_moves_uses_standard_notation():
    assert format_moves([Move.L3, Move.U3, Move.R2]) == "L' U' R2"


def test_parse_is_available_from_the_package():
    assert parse(SOLVED).corner == 0


def test_solve_returns_a_formatted_solution():
    assert solve(U_TURN, timeout=5) == "U'"


def test_solve_returns_none_when_the_bound_is_too_short():
    assert solve(U_TURN, max_length=0, timeout=5) is None


def test_solve_progressively_formats_each_solution():
    solutions = list(solve_progressively(U_TURN, timeout=5))
    assert solutions[-1] == "U'"
    assert all(isinstance(solution, str) for solution in solutions)


def test_solve_rejects_invalid_facelets():
    with pytest.raises(InvalidCube, match="54 characters"):
        solve("not a cube")
