from __future__ import annotations

import functools
import math
from dataclasses import dataclass
from enum import IntEnum
from typing import Callable, Iterator

from twophase.constants import (
    CORNER_MAX,
    EDGE4_MAX,
    EDGE8_MAX,
    FLIP_MAX,
    TWIST_MAX,
    UD_SLICE_MAX,
)
from twophase.exceptions import InvalidCube
from twophase.pieces import Corner, Edge

CORNER_PERM = tuple[Corner, ...]
PIECE_ORI = tuple[int, ...]
EDGE_PERM = tuple[Edge, ...]

SOLVED_CP = (
    Corner.URF,
    Corner.UFL,
    Corner.ULB,
    Corner.UBR,
    Corner.DFR,
    Corner.DLF,
    Corner.DBL,
    Corner.DRB,
)
SOLVED_CO = (0,) * 8
SOLVED_EP = (
    Edge.UR,
    Edge.UF,
    Edge.UL,
    Edge.UB,
    Edge.DR,
    Edge.DF,
    Edge.DL,
    Edge.DB,
    Edge.FR,
    Edge.FL,
    Edge.BL,
    Edge.BR,
)
SOLVED_EO = (0,) * 12

U_EDGES = [Edge.UR, Edge.UF, Edge.UL, Edge.UB]
UD_SLICE = [Edge.FR, Edge.FL, Edge.BL, Edge.BR]
D_EDGES = [Edge.DR, Edge.DF, Edge.DL, Edge.DB]


def _perm_to_coord(items: tuple[int | IntEnum, ...]) -> int:
    # maps each possible permutation of items onto 0, ..., len(items)! - 1

    # given a permutation p of (0, ..., n-1), for each i >= 1 we calulate how many
    # entries in p[:i] are greater than p[i]. call this number c_i
    # the coordinate is then calculated as 1! * c_1 + ... + (n-1)! * c_{n-1}

    # rather than calculate all the factorial numbers, we use a Horner-like algorithm
    # 1! * c_1 + ... + (n-1)! * c_{n-1} = 1 * (c_1 + 2 * (c_2 + 3 * (c_3 + ...)))
    out = 0
    n_items = len(items)
    for j in range(n_items - 1, 0, -1):
        out += sum(item > items[j] for item in items[:j])
        out *= j
    return out


def _coord_to_perm[T](coord: int, items: tuple[T, ...]) -> tuple[T, ...]:
    # given a coordinate and a number of items, recovers the permutation on n_items
    # that would get assigned that coordinate by _perm_to_coord

    # we first extract the coefficients which tell us for each i >= 1, how many entries
    # of p[:i] are greater than p[i], where p is the permutation we're trying to recover
    # starting from i = n - 1 we can determine each entry of p based on the coefficients
    # and by keeping track of which numbers have already been determined.
    item_list = list(items)
    n_items = len(items)

    coeffs = [0] * (n_items - 1)
    for i in range(1, n_items):
        coeffs[i - 1] = coord % (i + 1)
        coord //= i + 1

    perm: list[T] = [items[0]] * n_items
    for i in range(n_items - 1, 0, -1):
        perm[i] = item_list.pop(i - coeffs[i - 1])
    perm[0] = item_list[0]

    return tuple(perm)


def _slice_to_coord(edges: EDGE_PERM, slice_edges: set[Edge]) -> int:
    # maps the position of slice_edges within edges onto 0, ..., 494 = 12C4 - 1

    # given the locations (0, 1, 1, 0, 0, 1, 0, 0, 0, 0, 1, 0) of four edges in a
    # sequence of twelve, the coordinate is calculated by computing iC(s-1) at each 1,
    # where i is the index of the 1 counting from the right, and s is 1 for the first 1,
    # 2 for the second etc.
    coord, seen = 0, 0
    for i, edge in enumerate(reversed(edges)):
        if edge in slice_edges:
            seen += 1
            coord += math.comb(i, seen)
    return coord


def _coord_to_slice(
    coord: int, slice_edges: EDGE_PERM, other_edges: EDGE_PERM, offset: int = 0
) -> EDGE_PERM:
    # combines slice_edges and other_edges into a tuple, with the positions of the
    # slice_edges set in order that _slice_to_coord would recover coord.

    # to position the slice_edges, we subtract binomial coefficients from the coordinate
    # for as long as the result is non-negative. if we encounter a coefficient that is
    # larger than the remaining coordinate then we know we must have reached the next
    # location of a slice_edge.
    ep = [Edge.NULL] * 12
    # first we position the slice edges
    seen = len(slice_edges)
    for j in range(12):
        if coord - math.comb(11 - j, seen) >= 0:
            ep[j] = slice_edges[4 - seen]
            coord -= math.comb(11 - j, seen)
            seen -= 1

    # then position the remaining edges in order
    i = 0
    for j in range(12):
        if ep[j] == Edge.NULL:
            ep[j] = other_edges[i]
            i += 1

    return tuple(ep[offset:] + ep[:offset])


def _parity(items: tuple[IntEnum, ...]) -> int:
    # parity of a permutation is the number of swaps (mod 2) that need to be performed
    # to sort the items. since every permutation of the cube results in an even number
    # of swaps of pieces, the parity of the corner and edge permutations must be the
    # same for the cube to be solvable
    return sum(items[j] > items[i] for i in range(len(items)) for j in range(i)) % 2


def _range_check(max_val: int):
    # decorator to be used for input validation on coordinate setters
    def decorator[T](fn: Callable[[T, int], None]) -> Callable[[T, int], None]:
        name = getattr(fn, "__name__", repr(fn))

        @functools.wraps(fn)
        def wrapper(self: T, arg: int) -> None:
            if not 0 <= arg < max_val:
                raise ValueError(
                    f"{arg} is out of range for {name}. "
                    f"Choose a value in the range 0, ..., {max_val - 1}."
                )
            fn(self, arg)

        return wrapper

    return decorator


@dataclass
class CubieCube:
    cp: CORNER_PERM = SOLVED_CP
    co: PIECE_ORI = SOLVED_CO
    ep: EDGE_PERM = SOLVED_EP
    eo: PIECE_ORI = SOLVED_EO

    @property
    def twist(self) -> int:
        """
        Compute twist, the coordinate representing corner orientation. We take the
        orientation of the first 7 corners, represented as 0, 1 or 2 as there are three
        possibilities, and view that as a ternary number in the range 0, ..., 3^7 - 1.
        """
        twist = 0
        for co in self.co[:-1]:
            twist = 3 * twist + co
        return twist

    @twist.setter
    @_range_check(TWIST_MAX)
    def twist(self, twist: int) -> None:
        """
        Set the twist of the cube. Each of the values 0, ..., 3^7-1 determines
        a distinct way of orienting each of the 8 corners.

        Parameters
        ----------
        twist : int
            Orientation of the 8 corners encoded as twist coordinate. Must
            satisfy 0 <= twist < 3^7.
        """
        twist_parity = 0
        co = [0] * 8
        for i in range(7):
            twist, co[6 - i] = divmod(twist, 3)
            twist_parity += co[6 - i]
        co[7] = (-twist_parity) % 3
        self.co = tuple(co)

    @property
    def flip(self) -> int:
        """
        Compute flip, the coordinate representing edge orientation. We take the
        orientation of the first 11 edges, represented as 0 or 1 as there are two
        possibilities, and view that as a binary number in the range 0, ..., 2^11 - 1.
        """
        flip = 0
        for eo in self.eo[:-1]:
            flip = 2 * flip + eo
        return flip

    @flip.setter
    @_range_check(FLIP_MAX)
    def flip(self, flip: int) -> None:
        """
        Set the flip of the cube. Each of the values 0, ..., 2^11-1 determines a
        distinct way of orienting each of the 12 edges.

        Parameters
        ----------
        flip : int
            Orientation of the 12 corners encoded as flip coordinate. Must satisfy
            0 <= flip < 2^11.
        """
        flip_parity = 0
        eo = [0] * 12
        for i in range(11):
            flip, eo[10 - i] = divmod(flip, 2)
            flip_parity += eo[10 - i]
        eo[11] = (-flip_parity) % 2
        self.eo = tuple(eo)

    @property
    def ud_slice(self) -> int:
        """
        Compute ud_slice, the coordinate representing the location (but not
        permutation) of the edges FR, FL, BL, BR.
        """
        return _slice_to_coord(self.ep, set(UD_SLICE))

    @ud_slice.setter
    @_range_check(UD_SLICE_MAX)
    def ud_slice(self, ud_slice: int) -> None:
        """
        Set ud_slice. Each of the values 0, ..., 12C4 - 1 corresponds to a distinct way
        of placing the four edges FR, FL, BL, BR in the 12 edge locations of the cube.

        Parameters
        ----------
        ud_slice : int
            Position of the aforementioned edges encoded as ud_slice coordinate. Must
            satisfy 0 <= ud_slice < 12C4.
        """
        self.ep = _coord_to_slice(ud_slice, tuple(UD_SLICE), tuple(U_EDGES + D_EDGES))

    @property
    def flip_ud_slice(self) -> int:
        """
        Coordinate that combines flip and ud_slice into a single value.
        """
        return FLIP_MAX * self.ud_slice + self.flip

    @flip_ud_slice.setter
    @_range_check(FLIP_MAX * UD_SLICE_MAX)
    def flip_ud_slice(self, flip_ud_slice: int) -> None:
        """
        Jointly set ud_slice and flip coordinates. flip_ud_slice is assumed to take the
        form ud_slice * 2^11 + flip.

        Parameters
        ----------
        flip_ud_slice : int
            A coordinate combining flip and ud_slice coordinates. Must satisfy
            0 <= flip_ud_slice < 1_013_760.
        """
        ud_slice, flip = divmod(flip_ud_slice, FLIP_MAX)
        self.ud_slice = ud_slice
        self.flip = flip

    @property
    def ud_slice_sorted(self) -> int:
        """
        Compute ud_slice_sorted, the coordinate representing the location and
        permutation of the edges FR, FL, BL, BR.
        """
        return EDGE4_MAX * _slice_to_coord(self.ep, set(UD_SLICE)) + _perm_to_coord(
            tuple(edge for edge in self.ep if edge in set(UD_SLICE))
        )

    @ud_slice_sorted.setter
    @_range_check(math.comb(12, 4) * EDGE4_MAX)
    def ud_slice_sorted(self, ud_slice_sorted: int) -> None:
        """
        Set ud_slice_sorted. ud_slice_sorted // 24 is the ud_slice coordinate
        corresponding to the location of the edges FR, FL, BL, BR. ud_slice_sorted % 24
        is the relative permutation of those edges.

        Parameters
        ----------
        ud_slice_sorted : int
            Position and permutation of the aforementioned edges encoded as
            ud_slice_sorted coordinate. Must satisfy 0 <= ud_slice_sorted < 12C4 * 4!
        """
        ud_slice, edge4 = divmod(ud_slice_sorted, EDGE4_MAX)
        slice_edges = _coord_to_perm(edge4, tuple(UD_SLICE))
        self.ep = _coord_to_slice(ud_slice, slice_edges, tuple(U_EDGES + D_EDGES))

    @property
    def u_edges_sorted(self) -> int:
        """
        Compute ud_slice_sorted, the coordinate representing the location and
        permutation of the edges UR, UF, UL, UB.
        """
        # we reverse the edges for calculating the relative position, this means that
        # the u_edges_sorted coordinate will take values in 0, ..., 1679 in phase 2
        ep = tuple(self.ep)
        return EDGE4_MAX * _slice_to_coord(ep[::-1], set(U_EDGES)) + _perm_to_coord(
            tuple(edge for edge in ep if edge in set(U_EDGES))
        )

    @u_edges_sorted.setter
    @_range_check(math.comb(12, 4) * EDGE4_MAX)
    def u_edges_sorted(self, u_edges_sorted: int) -> None:
        """
        Set u_edges_sorted. u_edges_sorted // 24 is the ud_slice coordinate
        corresponding to the location of the edges UR, UF, UL, UB. u_edges_sorted % 24
        is the relative permutation of those edges.

        Parameters
        ----------
        u_edges_sorted : int
            Position and permutation of the aforementioned edges encoded as
            u_edges_sorted coordinate. Must satisfy 0 <= u_edges_sorted < 12C4 * 4!
        """
        u_edges, perm_coord = divmod(u_edges_sorted, EDGE4_MAX)
        perm = _coord_to_perm(perm_coord, tuple(U_EDGES))
        # reverse the u edges before placing them, so that when we reverse the full edge
        # permutation we end up with things the right way again. this messiness is to
        # make the transition to phase 2 easier by ensuring that the u edges do not
        # occupy the ud-slice for coordinates 0, ..., 1679
        self.ep = _coord_to_slice(
            u_edges, tuple(reversed(perm)), tuple(reversed(D_EDGES + UD_SLICE))
        )[::-1]

    @property
    def d_edges_sorted(self) -> int:
        """
        Compute ud_slice_sorted, the coordinate representing the location and
        permutation of the edges DR, DF, DL, DB.
        """
        ep = self.ep[8:] + self.ep[:8]
        return EDGE4_MAX * _slice_to_coord(ep, set(D_EDGES)) + _perm_to_coord(
            tuple(edge for edge in ep if edge in set(D_EDGES))
        )

    @d_edges_sorted.setter
    @_range_check(math.comb(12, 4) * EDGE4_MAX)
    def d_edges_sorted(self, d_edges_sorted: int) -> None:
        """
        Set d_edges_sorted. d_edges_sorted // 24 is the ud_slice coordinate
        corresponding to the location of the edges DR, DF, DL, DB. d_edges_sorted % 24
        is the relative permutation of those edges.

        Parameters
        ----------
        d_edges_sorted : int
            Position and permutation of the aforementioned edges encoded as
            d_edges_sorted coordinate. Must satisfy 0 <= d_edges_sorted < 12C4 * 4!
        """
        d_edges, perm_coord = divmod(d_edges_sorted, EDGE4_MAX)
        perm = _coord_to_perm(perm_coord, tuple(D_EDGES))
        self.ep = _coord_to_slice(d_edges, perm, tuple(UD_SLICE + U_EDGES), offset=4)

    @property
    def corner(self) -> int:
        """
        Compute corner, the coordinate representing permutation of the 8
        corners.

        There are 8 possible positions for the 8 corners, so corner takes
        values in the range 0, ..., 8! - 1.
        """
        return _perm_to_coord(self.cp)

    @corner.setter
    @_range_check(CORNER_MAX)
    def corner(self, corner: int) -> None:
        """
        Set the corner of the cube. Each of the values 0, ..., 8! - 1
        determines a distinct permutation of the 8 corners.

        Parameters
        ----------
        corner : int
            Order of the 8 corners encoded as corner coordinate. Must satisfy
            0 <= corner < 8!
        """
        self.cp = _coord_to_perm(corner, SOLVED_CP)

    @property
    def edge8(self) -> int:
        """
        Compute edge8, the coordinate representing permutation of the 8 edges
        UR, UF, UL, UB, DR, DF, DL, DB. In phase 2 these edges will all be in
        the U and D slices.

        There are 8 possible positions for the 8 edges, so edge8 takes values
        in the range 0, ..., 8! - 1.
        """
        return _perm_to_coord(self.ep[:8])

    @edge8.setter
    @_range_check(EDGE8_MAX)
    def edge8(self, edge8: int) -> None:
        """
        Set the edge8 of the cube. Each of the values 0, ..., 8! - 1 determines
        a distinct order of the 8 edges UR, UF, UL, UB, DR, DF, DL, DB in the U
        and D slices during phase 2.

        Parameters
        ----------
        edge8 : int
            Order of the 8 aforementioned edges encoded as edge8 coordinate.
            Must satisfy 0 <= edge8 < 8!
        """
        self.ep = _coord_to_perm(edge8, SOLVED_EP[:8]) + self.ep[8:]

    @property
    def corner_parity(self) -> int:
        """
        Corner parity of the CubieCube. The number of corner swaps that must be
        performed to reach the solved state. A cube is solvable if and only if the
        corner parity matches the edge parity.
        """
        return _parity(self.cp)

    @property
    def edge_parity(self) -> int:
        """
        Edge parity of the CubieCube. The number of edge swaps that must be performed
        to reach the solved state. A cube is solvable if and only if the edge parity
        matches the corner parity.
        """
        return _parity(self.ep)

    @staticmethod
    def _corner_orientation(ori_self, ori_move):
        # if self is mirrored, subtract orientations of move, otherwise update as usual
        ori = ori_self + ori_move if ori_self < 3 else ori_self - ori_move
        if (ori_self < 3) ^ (ori_move < 3):
            # result is mirrored cube
            return (ori % 3) + 3
        return ori % 3

    def corner_multiply(self, move: CubieCube) -> CubieCube:
        return CubieCube(
            cp=tuple(self.cp[move.cp[i]] for i in range(8)),
            co=tuple(
                self._corner_orientation(self.co[move.cp[i]], move.co[i])
                for i in range(8)
            ),
            ep=self.ep,
            eo=self.eo,
        )

    def edge_multiply(self, move: CubieCube) -> CubieCube:
        return CubieCube(
            cp=self.cp,
            co=self.co,
            ep=tuple(self.ep[move.ep[i]] for i in range(12)),
            eo=tuple((self.eo[move.ep[i]] + move.eo[i]) % 2 for i in range(12)),
        )

    def multiply(self, move: CubieCube) -> CubieCube:
        # while we could chain corner_multiple and edge_multiply, it's slightly more
        # efficient to do it all in one go even though it means some code duplication
        return CubieCube(
            cp=tuple(self.cp[move.cp[i]] for i in range(8)),
            co=tuple(
                self._corner_orientation(self.co[move.cp[i]], move.co[i])
                for i in range(8)
            ),
            ep=tuple(self.ep[move.ep[i]] for i in range(12)),
            eo=tuple((self.eo[move.ep[i]] + move.eo[i]) % 2 for i in range(12)),
        )

    def __mul__(self, move: CubieCube) -> CubieCube:
        return self.multiply(move)

    def invert(self) -> CubieCube:
        """
        Calculate the inverse of the given CubieCube.
        """
        ep = [Edge.NULL] * 12
        eo = [-1] * 12
        for edge in SOLVED_EP:
            ep[self.ep[edge]] = edge
        for edge in SOLVED_EP:
            eo[edge] = self.eo[ep[edge]]

        cp = [Corner.NULL] * 8
        co = [-1] * 8
        for corner in SOLVED_CP:
            cp[self.cp[corner]] = corner
        for corner in SOLVED_CP:
            ori = self.co[cp[corner]]
            co[corner] = ori if ori >= 3 else (-ori % 3)

        return CubieCube(cp=tuple(cp), co=tuple(co), ep=tuple(ep), eo=tuple(eo))


_MOVE_U = CubieCube(
    cp=(
        Corner.UBR,
        Corner.URF,
        Corner.UFL,
        Corner.ULB,
        Corner.DFR,
        Corner.DLF,
        Corner.DBL,
        Corner.DRB,
    ),
    co=(0,) * 8,
    ep=(
        Edge.UB,
        Edge.UR,
        Edge.UF,
        Edge.UL,
        Edge.DR,
        Edge.DF,
        Edge.DL,
        Edge.DB,
        Edge.FR,
        Edge.FL,
        Edge.BL,
        Edge.BR,
    ),
    eo=(0,) * 12,
)
_MOVE_R = CubieCube(
    cp=(
        Corner.DFR,
        Corner.UFL,
        Corner.ULB,
        Corner.URF,
        Corner.DRB,
        Corner.DLF,
        Corner.DBL,
        Corner.UBR,
    ),
    co=(2, 0, 0, 1, 1, 0, 0, 2),
    ep=(
        Edge.FR,
        Edge.UF,
        Edge.UL,
        Edge.UB,
        Edge.BR,
        Edge.DF,
        Edge.DL,
        Edge.DB,
        Edge.DR,
        Edge.FL,
        Edge.BL,
        Edge.UR,
    ),
    eo=(0,) * 12,
)
_MOVE_F = CubieCube(
    cp=(
        Corner.UFL,
        Corner.DLF,
        Corner.ULB,
        Corner.UBR,
        Corner.URF,
        Corner.DFR,
        Corner.DBL,
        Corner.DRB,
    ),
    co=(1, 2, 0, 0, 2, 1, 0, 0),
    ep=(
        Edge.UR,
        Edge.FL,
        Edge.UL,
        Edge.UB,
        Edge.DR,
        Edge.FR,
        Edge.DL,
        Edge.DB,
        Edge.UF,
        Edge.DF,
        Edge.BL,
        Edge.BR,
    ),
    eo=(0, 1, 0, 0, 0, 1, 0, 0, 1, 1, 0, 0),
)
_MOVE_D = CubieCube(
    cp=(
        Corner.URF,
        Corner.UFL,
        Corner.ULB,
        Corner.UBR,
        Corner.DLF,
        Corner.DBL,
        Corner.DRB,
        Corner.DFR,
    ),
    co=(0,) * 8,
    ep=(
        Edge.UR,
        Edge.UF,
        Edge.UL,
        Edge.UB,
        Edge.DF,
        Edge.DL,
        Edge.DB,
        Edge.DR,
        Edge.FR,
        Edge.FL,
        Edge.BL,
        Edge.BR,
    ),
    eo=(0,) * 12,
)
_MOVE_L = CubieCube(
    cp=(
        Corner.URF,
        Corner.ULB,
        Corner.DBL,
        Corner.UBR,
        Corner.DFR,
        Corner.UFL,
        Corner.DLF,
        Corner.DRB,
    ),
    co=(0, 1, 2, 0, 0, 2, 1, 0),
    ep=(
        Edge.UR,
        Edge.UF,
        Edge.BL,
        Edge.UB,
        Edge.DR,
        Edge.DF,
        Edge.FL,
        Edge.DB,
        Edge.FR,
        Edge.UL,
        Edge.DL,
        Edge.BR,
    ),
    eo=(0,) * 12,
)
_MOVE_B = CubieCube(
    cp=(
        Corner.URF,
        Corner.UFL,
        Corner.UBR,
        Corner.DRB,
        Corner.DFR,
        Corner.DLF,
        Corner.ULB,
        Corner.DBL,
    ),
    co=(0, 0, 1, 2, 0, 0, 2, 1),
    ep=(
        Edge.UR,
        Edge.UF,
        Edge.UL,
        Edge.BR,
        Edge.DR,
        Edge.DF,
        Edge.DL,
        Edge.BL,
        Edge.FR,
        Edge.FL,
        Edge.UB,
        Edge.DB,
    ),
    eo=(0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 1, 1),
)

_MOVES = [_MOVE_U, _MOVE_R, _MOVE_F, _MOVE_D, _MOVE_L, _MOVE_B]


class Moves:
    _moves: tuple[CubieCube, ...] = ()

    def __new__(cls) -> Moves:
        if not cls._moves:
            moves: list[CubieCube] = []
            for mv in _MOVES:
                cube = CubieCube()
                for _ in range(3):
                    cube *= mv
                    moves.append(cube)
            cls._moves = tuple(moves)

        return super().__new__(cls)

    def __getitem__(self, idx: int | slice) -> CubieCube | tuple[CubieCube, ...]:
        return self._moves[idx]

    def __len__(self) -> int:
        return len(self._moves)

    def __iter__(self) -> Iterator[CubieCube]:
        return iter(self._moves)


def move(cube: CubieCube, i: int, corner: bool = True, edge: bool = True) -> CubieCube:
    if corner:
        if edge:
            return cube.multiply(_MOVES[i])
        return cube.corner_multiply(_MOVES[i])
    elif edge:
        return cube.edge_multiply(_MOVES[i])
    raise ValueError("At least one of corner and edge must be set to True")


def verify(cube: CubieCube) -> None:
    # check all pieces appear exactly once
    edges = set()
    for edge in cube.ep:
        if edge in edges:
            raise InvalidCube(f"{edge!r} appears more than once")
        edges.add(edge)

    corners = set()
    for corner in cube.cp:
        if corner in corners:
            raise InvalidCube(f"{corner!r} appears more than once")
        corners.add(corner)

    # check orientation of pieces
    if sum(cube.eo) % 2 != 0:
        raise InvalidCube("Flip error: an edge must be flipped")
    if sum(cube.co) % 3 != 0:
        raise InvalidCube("Twist error: a corner must be twisted")

    # check parity / compatibility of edges and corners
    if cube.edge_parity != cube.corner_parity:
        raise InvalidCube("Parity error: two edges or two corners must be swapped.")
