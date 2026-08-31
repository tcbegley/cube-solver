"""An educational implementation of Kociemba's two-phase cube solver."""

from importlib.metadata import PackageNotFoundError, version

from twophase.cubestring import parse
from twophase.interface import solve, solve_progressively
from twophase.pieces import Color, Corner, Edge, Facelet, Move, format_moves
from twophase.solve.solver import Solver
from twophase.tables.cubiecube import CubieCube

try:
    __version__ = version("twophase")
except PackageNotFoundError:
    __version__ = "0.2.0+fallback"

__all__ = [
    "Color",
    "Corner",
    "CubieCube",
    "Edge",
    "Facelet",
    "Move",
    "Solver",
    "__version__",
    "format_moves",
    "parse",
    "solve",
    "solve_progressively",
]
