"""Convenient string-based entry points for the two-phase solver."""

from collections.abc import Generator
from pathlib import Path

from twophase.cubestring import parse
from twophase.pieces import format_moves
from twophase.solve.solver import Solver


def solve(
    cube_string: str,
    max_length: int = 20,
    timeout: float = 10.0,
    cache_path: str | Path | None = None,
) -> str | None:
    """Solve a facelet string and return its solution in standard cube notation.

    ``None`` is returned when no solution is found within ``max_length`` before
    ``timeout`` expires. Invalid facelet strings raise :class:`InvalidCube`.
    """
    cube = parse(cube_string)
    moves = Solver(cache_path).solve(cube, max_length, timeout)
    return None if moves is None else format_moves(moves)


def solve_progressively(
    cube_string: str,
    max_length: int = 20,
    timeout: float = 10.0,
    cache_path: str | Path | None = None,
) -> Generator[str]:
    """Yield successively shorter solutions for a facelet string."""
    cube = parse(cube_string)
    solver = Solver(cache_path)
    yield from (
        format_moves(moves)
        for moves in solver.solve_progressively(cube, max_length, timeout)
    )
