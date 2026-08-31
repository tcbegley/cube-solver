"""
Parse a cube definition string into a CubieCube.

A cube string is a 54-character string specifying the sticker colour on each
facelet, reading each face (U R F D L B) row by row from top-left to
bottom-right::

    Face layout:         Facelet numbering:

         U U U                1 2 3
         U U U                4 5 6
         U U U                7 8 9
    L L L F F F R R R B B B
    L L L F F F R R R B B B
    L L L F F F R R R B B B
         D D D
         D D D
         D D D

Valid characters are the face letters ``U R F D L B`` (case-insensitive).

Example
-------
The solved cube:

>>> from twophase.cubestring import parse
>>> cc = parse("UUUUUUUUURRRRRRRRRFFFFFFFFFDDDDDDDDDLLLLLLLLLBBBBBBBBB")
"""

from twophase.exceptions import InvalidCube
from twophase.pieces import Color, Corner, Edge, Facelet
from twophase.tables.cubiecube import CubieCube, verify

_CORNER_FACELETS: tuple[tuple[Facelet, Facelet, Facelet], ...] = (
    (Facelet.U9, Facelet.R1, Facelet.F3),  # URF
    (Facelet.U7, Facelet.F1, Facelet.L3),  # UFL
    (Facelet.U1, Facelet.L1, Facelet.B3),  # ULB
    (Facelet.U3, Facelet.B1, Facelet.R3),  # UBR
    (Facelet.D3, Facelet.F9, Facelet.R7),  # DFR
    (Facelet.D1, Facelet.L9, Facelet.F7),  # DLF
    (Facelet.D7, Facelet.B9, Facelet.L7),  # DBL
    (Facelet.D9, Facelet.R9, Facelet.B7),  # DRB
)

_EDGE_FACELETS: tuple[tuple[Facelet, Facelet], ...] = (
    (Facelet.U6, Facelet.R2),  # UR
    (Facelet.U8, Facelet.F2),  # UF
    (Facelet.U4, Facelet.L2),  # UL
    (Facelet.U2, Facelet.B2),  # UB
    (Facelet.D6, Facelet.R8),  # DR
    (Facelet.D2, Facelet.F8),  # DF
    (Facelet.D4, Facelet.L8),  # DL
    (Facelet.D8, Facelet.B8),  # DB
    (Facelet.F6, Facelet.R4),  # FR
    (Facelet.F4, Facelet.L6),  # FL
    (Facelet.B6, Facelet.L4),  # BL
    (Facelet.B4, Facelet.R6),  # BR
)

# The colours that appear on each piece in the solved state. Corner colours
# are ordered (U/D face, clockwise, clockwise) matching _CORNER_FACELETS.
_CORNER_COLORS: tuple[tuple[Color, Color, Color], ...] = (
    (Color.U, Color.R, Color.F),  # URF
    (Color.U, Color.F, Color.L),  # UFL
    (Color.U, Color.L, Color.B),  # ULB
    (Color.U, Color.B, Color.R),  # UBR
    (Color.D, Color.F, Color.R),  # DFR
    (Color.D, Color.L, Color.F),  # DLF
    (Color.D, Color.B, Color.L),  # DBL
    (Color.D, Color.R, Color.B),  # DRB
)

_EDGE_COLORS: tuple[tuple[Color, Color], ...] = (
    (Color.U, Color.R),  # UR
    (Color.U, Color.F),  # UF
    (Color.U, Color.L),  # UL
    (Color.U, Color.B),  # UB
    (Color.D, Color.R),  # DR
    (Color.D, Color.F),  # DF
    (Color.D, Color.L),  # DL
    (Color.D, Color.B),  # DB
    (Color.F, Color.R),  # FR
    (Color.F, Color.L),  # FL
    (Color.B, Color.L),  # BL
    (Color.B, Color.R),  # BR
)


def parse(cube_string: str) -> CubieCube:
    """Parse a 54-character cube string into a ``CubieCube``.

    Parameters
    ----------
    cube_string
        A 54-character string of face letters (``U R F D L B``,
        case-insensitive) describing the sticker on each facelet.

    Returns
    -------
    CubieCube
        The cube in cubie-level representation.

    Raises
    ------
    InvalidCube
        If the string is malformed or does not describe a valid cube.
    """
    facelets = _parse_facelets(cube_string)
    cp, co = _extract_corners(facelets)
    ep, eo = _extract_edges(facelets)

    cube = CubieCube(cp=tuple(cp), co=tuple(co), ep=tuple(ep), eo=tuple(eo))
    verify(cube)
    return cube


def _parse_facelets(cube_string: str) -> list[Color]:
    """
    Validate and convert a cube string into a list of 54 Colors.
    """
    cube_string = cube_string.upper()
    if len(cube_string) != 54:
        raise InvalidCube(
            f"cube string must be exactly 54 characters, got {len(cube_string)}"
        )

    counts = [0] * 6
    facelets: list[Color] = []
    for char in cube_string:
        try:
            color = Color[char]
        except KeyError:
            raise InvalidCube(f"invalid character {char!r} in cube string") from None
        counts[color] += 1
        facelets.append(color)

    for color in Color:
        if color == Color.NULL:
            continue
        if counts[color] != 9:
            raise InvalidCube(
                f"each colour must appear exactly 9 times, "
                f"but {color.name} appears {counts[color]} times"
            )

    return facelets


def _extract_corners(facelets: list[Color]) -> tuple[list[Corner], list[int]]:
    """
    Determine corner permutation and orientation from facelets.
    """
    cp: list[Corner] = [Corner.NULL] * 8
    co: list[int] = [0] * 8

    for i in range(8):
        f0, f1, f2 = _CORNER_FACELETS[i]

        # find which of the three facelets carries the U or D colour — that
        # tells us the orientation (0 = no twist, 1 = clockwise, 2 = counter)
        for orientation in range(3):
            if facelets[(f0, f1, f2)[orientation]] in (Color.U, Color.D):
                break
        else:
            raise InvalidCube(f"corner at position {i} has no U/D facelet")

        # read the other two colours in clockwise order from the U/D facelet
        color1 = facelets[(f0, f1, f2)[(orientation + 1) % 3]]
        color2 = facelets[(f0, f1, f2)[(orientation + 2) % 3]]

        # match against the known corner colour patterns
        for j in range(8):
            if color1 == _CORNER_COLORS[j][1] and color2 == _CORNER_COLORS[j][2]:
                cp[i] = Corner(j)
                co[i] = orientation
                break
        else:
            raise InvalidCube(f"corner at position {i} has unrecognised colours")

    return cp, co


def _extract_edges(facelets: list[Color]) -> tuple[list[Edge], list[int]]:
    """
    Determine edge permutation and orientation from facelets.
    """
    ep: list[Edge] = [Edge.NULL] * 12
    eo: list[int] = [0] * 12

    for i in range(12):
        f0, f1 = _EDGE_FACELETS[i]
        c0, c1 = facelets[f0], facelets[f1]

        for j in range(12):
            if c0 == _EDGE_COLORS[j][0] and c1 == _EDGE_COLORS[j][1]:
                ep[i] = Edge(j)
                eo[i] = 0
                break
            if c0 == _EDGE_COLORS[j][1] and c1 == _EDGE_COLORS[j][0]:
                ep[i] = Edge(j)
                eo[i] = 1
                break
        else:
            raise InvalidCube(f"edge at position {i} has unrecognised colours")

    return ep, eo
