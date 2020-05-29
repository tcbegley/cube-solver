"""
This class describes cubes on the level of the cubies.
"""
from functools import reduce

from ..pieces import Corner, Edge
from . import facecube


def choose(n, k):
    """
    A fast way to compute binomial coefficients by Andrew Dalke.
    """
    if 0 <= k <= n:
        num = 1
        den = 1
        for i in range(1, min(k, n - k) + 1):
            num *= n
            den *= i
            n -= 1
        return num // den
    else:
        return 0


# Moves on the cubie level, gives permutation and orientation after the moves
# U, R, F, D, L, B resp from a clean cube. This will be used to compute move
# tables and the composition rules.
_cpU = (
    Corner.UBR,
    Corner.URF,
    Corner.UFL,
    Corner.ULB,
    Corner.DFR,
    Corner.DLF,
    Corner.DBL,
    Corner.DRB,
)
_coU = (0, 0, 0, 0, 0, 0, 0, 0)
_epU = (
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
)
_eoU = (0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)

_cpR = (
    Corner.DFR,
    Corner.UFL,
    Corner.ULB,
    Corner.URF,
    Corner.DRB,
    Corner.DLF,
    Corner.DBL,
    Corner.UBR,
)
_coR = (2, 0, 0, 1, 1, 0, 0, 2)
_epR = (
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
)
_eoR = (0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)

_cpF = (
    Corner.UFL,
    Corner.DLF,
    Corner.ULB,
    Corner.UBR,
    Corner.URF,
    Corner.DFR,
    Corner.DBL,
    Corner.DRB,
)
_coF = (1, 2, 0, 0, 2, 1, 0, 0)
_epF = (
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
)
_eoF = (0, 1, 0, 0, 0, 1, 0, 0, 1, 1, 0, 0)

_cpD = (
    Corner.URF,
    Corner.UFL,
    Corner.ULB,
    Corner.UBR,
    Corner.DLF,
    Corner.DBL,
    Corner.DRB,
    Corner.DFR,
)
_coD = (0, 0, 0, 0, 0, 0, 0, 0)
_epD = (
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
)
_eoD = (0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)

_cpL = (
    Corner.URF,
    Corner.ULB,
    Corner.DBL,
    Corner.UBR,
    Corner.DFR,
    Corner.UFL,
    Corner.DLF,
    Corner.DRB,
)
_coL = (0, 1, 2, 0, 0, 2, 1, 0)
_epL = (
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
)
_eoL = (0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)

_cpB = (
    Corner.URF,
    Corner.UFL,
    Corner.UBR,
    Corner.DRB,
    Corner.DFR,
    Corner.DLF,
    Corner.ULB,
    Corner.DBL,
)
_coB = (0, 0, 1, 2, 0, 0, 2, 1)
_epB = (
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
)
_eoB = (0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 1, 1)


class CubieCube:
    def __init__(self, cp=None, co=None, ep=None, eo=None):
        if cp and co and ep and eo:
            self.cp = cp[:]
            self.co = co[:]
            self.ep = ep[:]
            self.eo = eo[:]
        else:
            # Initialise clean cube if position not given.
            self.cp = [
                Corner.URF,
                Corner.UFL,
                Corner.ULB,
                Corner.UBR,
                Corner.DFR,
                Corner.DLF,
                Corner.DBL,
                Corner.DRB,
            ]
            self.co = [0, 0, 0, 0, 0, 0, 0, 0]
            self.ep = [
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
            ]
            self.eo = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]

    def corner_multiply(self, b):
        """
        Compute permutation and orientation of corners after applying
        permutation represented by b to current cube.

        Parameters
        ----------
        b : CubieCube
            Permutation to apply represented as a CubieCube.

        Notes
        -----
        We use "is replaced by" notation for the permutations. So b.cp[URF]
        gives the index of the piece that replaces URF when applying b. To
        explain the rules we use the example of first applying F then applying
        R.

        Under F we have URF<-UFL and under R we have UBR<-URF. Hence under FR
        we have UBR<-UFL, leading to the rule

        (F*R).cp[UBR] = F.cp[R.cp[UBR]]

        The corner orientation arrays tell us the change in orientation of a
        piece (based on where it ends up) due to that move. So for example
        F.co[URF] = 1, which means that as UFL moves to URF under the F move,
        its orientation increases by 1. To get the total change in orientation
        of the piece that moves to UBR under FR we use the rule

        (F*R).co[UBR] = F.co[R.cp[UBR]] + R.co[UBR].
        """
        corner_perm = [self.cp[b.cp[i]] for i in range(8)]
        corner_ori = [(self.co[b.cp[i]] + b.co[i]) % 3 for i in range(8)]
        self.co = corner_ori[:]
        self.cp = corner_perm[:]

    def edge_multiply(self, b):
        """
        Compute permutation and orientation of edges after applying permutation
        represented by b to current cube.

        Parameters
        ----------
        b : CubieCube
            Permutation to apply represented as a CubieCube.

        Notes
        -----
        See docstring of corner_multiply (which operates analogously to this
        method) for a description of how the update rules are derived.
        """
        edge_perm = [self.ep[b.ep[i]] for i in range(12)]
        edge_ori = [(self.eo[b.ep[i]] + b.eo[i]) % 2 for i in range(12)]
        self.eo = edge_ori[:]
        self.ep = edge_perm[:]

    def multiply(self, b):
        """
        Compute permutation and orientation of edges and corners after applying
        permutation represented by b to the current cube.

        Parameters
        ----------
        b : CubieCube
            Permutation to apply represented as a CubieCube
        """
        self.corner_multiply(b)
        self.edge_multiply(b)

    def move(self, i):
        """
        Helper function for applying one of 6 canonical moves
        """
        self.multiply(MOVE_CUBE[i])

    def inverse_cubiecube(self):
        """
        Compute the inverse of the current cube.
        """
        cube = CubieCube()
        for e in range(12):
            cube.ep[self.ep[e]] = e
        for e in range(12):
            cube.eo[e] = self.eo[cube.ep[e]]
        for c in range(8):
            cube.cp[self.cp[c]] = c
        for c in range(8):
            ori = self.co[cube.cp[c]]
            cube.co[c] = (-ori) % 3
        return cube

    def to_facecube(self):
        """
        Convert CubieCube to FaceCube.
        """
        ret = facecube.FaceCube()
        for i in range(8):
            j = self.cp[i]
            ori = self.co[i]
            for k in range(3):
                ret.f[
                    facecube.corner_facelet[i][(k + ori) % 3]
                ] = facecube.corner_color[j][k]
        for i in range(12):
            j = self.ep[i]
            ori = self.eo[i]
            for k in range(2):
                facelet_index = facecube.edge_facelet[i][(k + ori) % 2]
                ret.f[facelet_index] = facecube.edge_color[j][k]
        return ret

    @property
    def corner_parity(self):
        """
        Corner parity of the CubieCube. Cube is solveable if and only if this
        matches the edge parity.
        """
        s = 0
        for i in range(7, 0, -1):
            for j in range(i - 1, -1, -1):
                if self.cp[j] > self.cp[i]:
                    s += 1
        return s % 2

    @property
    def edge_parity(self):
        """
        Edge parity of the CubieCube. Cube is solveable if and only if this
        matches the corner parity.
        """
        s = 0
        for i in range(11, 0, -1):
            for j in range(i - 1, -1, -1):
                if self.ep[j] > self.ep[i]:
                    s += 1
        return s % 2

    # ----------   Phase 1 Coordinates  ---------- #
    @property
    def twist(self):
        """
        Compute twist, the coordinate representing corner orientation. We take
        the orientation of the first 7 corners, represented as 0, 1 or 2 as
        there are three possibilities, and view that as a ternary number in the
        range 0, ..., 3^7 - 1.

        Notes
        -----
        The orientation of the first eleven corners determines the orientation
        of the last, hence we only include the orientation of the first 7
        corners in the calculation of twist.
        """
        return reduce(lambda x, y: 3 * x + y, self.co[:7])

    @twist.setter
    def twist(self, twist):
        """
        Set the twist of the cube. Each of the values 0, ..., 3^7-1 determines
        a distinct way of orienting each of the 8 corners.

        Parameters
        ----------
        twist : int
            Orientation of the 8 corners encoded as twist coordinate. Must
            satisfy 0 <= twist < 3^7.
        """
        if not 0 <= twist < 3 ** 7:
            raise ValueError(
                "{} is out of range for twist, must take values in "
                "0, ..., 2186.".format(twist)
            )
        total = 0
        for i in range(7):
            x = twist % 3
            self.co[6 - i] = x
            total += x
            twist //= 3
        self.co[7] = (-total) % 3

    @property
    def flip(self):
        """
        Compute flip, the coordinate representing edge orientation. We take
        the orientation of the first 11 edges, represented as 0 or 1 as there
        are two possibilities, and view that as a binary number in the range
        0, ..., 2^11 - 1.

        Notes
        -----
        The orientation of the first eleven edges determines the orientation
        of the last, hence we only include the orientation of the first 11
        edges in the calculation of flip.
        """
        return reduce(lambda x, y: 2 * x + y, self.eo[:11])

    @flip.setter
    def flip(self, flip):
        """
        Set the flip of the cube. Each of the values 0, ..., 2^11-1 determines
        a distinct way of orienting each of the 12 edges.

        Parameters
        ----------
        flip : int
            Orientation of the 12 corners encoded as flip coordinate. Must
            satisfy 0 <= flip < 2^11.
        """
        if not 0 <= flip < 2 ** 11:
            raise ValueError(
                "{} is out of range for flip, must take values in "
                "0, ..., 2047.".format(flip)
            )
        total = 0
        for i in range(11):
            x = flip % 2
            self.eo[10 - i] = x
            total += x
            flip //= 2
        self.eo[11] = (-total) % 2

    @property
    def udslice(self):
        """
        Compute udslice, the coordinate representing position, but not the
        order, of the 4 edges FR, FL, BL, BR. These 4 edges must be in the
        middle layer for phase 2 to begin. If they are in the middle layer,
        udslice will have the value 0.

        Since there are 12 possible positions and we care only about those 4
        edges, udslice takes values in the range 0, ..., 12C4 - 1.
        """
        udslice, seen = 0, 0
        for j in range(12):
            if 8 <= self.ep[j] < 12:
                seen += 1
            elif seen >= 1:
                udslice += choose(j, seen - 1)
        return udslice

    @udslice.setter
    def udslice(self, udslice):
        """
        Set the udslice of the cube. Each of the values 0, ..., 12C4 - 1
        determines a distinct set of 4 positions for the edges FR, FL, BL, BR
        to occupy. Note that it does not determine the order of these edges.

        Parameters
        ----------
        udslice : int
            Position of the 4 aforementioned edges encoded as udslice
            coordinate. Must satisfy 0 <= slice < 12C4.
        """
        if not 0 <= udslice < choose(12, 4):
            raise ValueError(
                "{} is out of range for udslice, must take values in "
                "0, ..., 494.".format(udslice)
            )
        udslice_edge = [Edge.FR, Edge.FL, Edge.BL, Edge.BR]
        other_edge = [
            Edge.UR,
            Edge.UF,
            Edge.UL,
            Edge.UB,
            Edge.DR,
            Edge.DF,
            Edge.DL,
            Edge.DB,
        ]
        # invalidate edges
        for i in range(12):
            self.ep[i] = Edge.DB
        # we first position the slice edges
        seen = 3
        for j in range(11, -1, -1):
            if udslice - choose(j, seen) < 0:
                self.ep[j] = udslice_edge[seen]
                seen -= 1
            else:
                udslice -= choose(j, seen)
        # then the remaining edges
        x = 0
        for j in range(12):
            if self.ep[j] == Edge.DB:
                self.ep[j] = other_edge[x]
                x += 1

    # ----------  Phase 2 Coordinates  ---------- #
    @property
    def edge4(self):
        """
        Compute edge4, the coordinate representing permutation of the 4 edges
        FR, FL, BL, FR. This assumes that the cube is in phase 2 position, so
        in particular the 4 edges are correctly placed, just perhaps not
        correctly ordered. edge4 takes values in the range 0, ..., 4! - 1 = 23.
        """
        edge4 = self.ep[8:]
        ret = 0
        for j in range(3, 0, -1):
            s = 0
            for i in range(j):
                if edge4[i] > edge4[j]:
                    s += 1
            ret = j * (ret + s)
        return ret

    @edge4.setter
    def edge4(self, edge4):
        """
        Set the edge4 of the cube. Each of the values 0, ..., 4! - 1 determines
        a distinct order of the 4 edges FR, FL, BL, BR in the middle slice
        during phase 2.

        Parameters
        ----------
        edge4 : int
            Order of the 4 aforementioned edges encoded as edge4 coordinate.
            Must satisfy 0 <= edge4 < 4!
        """
        if not 0 <= edge4 < 24:
            raise ValueError(
                f"{edge4} is out of range for edge4, must take values in 0-23"
            )
        sliceedge = [Edge.FR, Edge.FL, Edge.BL, Edge.BR]
        coeffs = [0] * 3
        for i in range(1, 4):
            coeffs[i - 1] = edge4 % (i + 1)
            edge4 //= i + 1
        perm = [0] * 4
        for i in range(2, -1, -1):
            perm[i + 1] = sliceedge.pop(i + 1 - coeffs[i])
        perm[0] = sliceedge[0]
        self.ep[8:] = perm[:]

    @property
    def edge8(self):
        """
        Compute edge8, the coordinate representing permutation of the 8 edges
        UR, UF, UL, UB, DR, DF, DL, DB. In phase 2 these edges will all be in
        the U and D slices.

        There are 8 possible positions for the 8 edges, so edge8 takes values
        in the range 0, ..., 8! - 1.
        """
        edge8 = 0
        for j in range(7, 0, -1):
            s = 0
            for i in range(j):
                if self.ep[i] > self.ep[j]:
                    s += 1
            edge8 = j * (edge8 + s)
        return edge8

    @edge8.setter
    def edge8(self, edge8):
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
        edges = list(range(8))
        perm = [0] * 8
        coeffs = [0] * 7
        for i in range(1, 8):
            coeffs[i - 1] = edge8 % (i + 1)
            edge8 //= i + 1
        for i in range(6, -1, -1):
            perm[i + 1] = edges.pop(i + 1 - coeffs[i])
        perm[0] = edges[0]
        self.ep[:8] = perm[:]

    @property
    def corner(self):
        """
        Compute corner, the coordinate representing permutation of the 8
        corners.

        There are 8 possible positions for the 8 corners, so corner takes
        values in the range 0, ..., 8! - 1.
        """
        c = 0
        for j in range(7, 0, -1):
            s = 0
            for i in range(j):
                if self.cp[i] > self.cp[j]:
                    s += 1
            c = j * (c + s)
        return c

    @corner.setter
    def corner(self, corn):
        """
        Set the corner of the cube. Each of the values 0, ..., 8! - 1
        determines a distinct permutation of the 8 corners.

        Parameters
        ----------
        corner : int
            Order of the 8 corners encoded as corner coordinate. Must satisfy
            0 <= corner < 8!
        """
        corners = list(range(8))
        perm = [0] * 8
        coeffs = [0] * 7
        for i in range(1, 8):
            coeffs[i - 1] = corn % (i + 1)
            corn //= i + 1
        for i in range(6, -1, -1):
            perm[i + 1] = corners.pop(i + 1 - coeffs[i])
        perm[0] = corners[0]
        self.cp = perm[:]

    # ---------- Misc. Coordinates ---------- #

    # edge permutation coordinate not used in solving,
    # but needed to generate random cubes
    @property
    def edge(self):
        """
        Compute edge, the coordinate representing permutation of the 12
        corners.

        There are 12 possible positions for the 12 edges, so edge takes values
        in the range 0, ..., 12! - 1.
        """
        e = 0
        for j in range(11, 0, -1):
            s = 0
            for i in range(j):
                if self.ep[i] > self.ep[j]:
                    s += 1
            e = j * (e + s)
        return e

    @edge.setter
    def edge(self, edge):
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
        edges = list(range(12))
        perm = [0] * 12
        coeffs = [0] * 11
        for i in range(1, 12):
            coeffs[i - 1] = edge % (i + 1)
            edge //= i + 1
        for i in range(10, -1, -1):
            perm[i + 1] = edges.pop(i + 1 - coeffs[i])
        perm[0] = edges[0]
        self.ep = perm[:]

    # ----------  Solvability Check ---------- #

    # Check a cubiecube for solvability
    #
    def verify(self):
        """
        Check if current cube position is solvable.

        Returns
        -------
        int:
            Integer encoding solvability of cube.
                0: Solvable
                -2: not all 12 edges exist exactly once
                -3: flip error: one edge should be flipped
                -4: not all corners exist exactly once
                -5: twist error - a corner must be twisted
                -6: Parity error - two corners or edges have to be exchanged
        """
        total = 0
        edge_count = [0 for i in range(12)]
        for e in range(12):
            edge_count[self.ep[e]] += 1
        for i in range(12):
            if edge_count[i] != 1:
                return -2
        for i in range(12):
            total += self.eo[i]
        if total % 2 != 0:
            return -3
        corner_count = [0] * 8
        for c in range(8):
            corner_count[self.cp[c]] += 1
        for i in range(8):
            if corner_count[i] != 1:
                return -4
        total = 0
        for i in range(8):
            total += self.co[i]
        if total % 3 != 0:
            return -5
        if self.edge_parity != self.corner_parity:
            return -6
        return 0


# we store the six possible clockwise 1/4 turn moves in the following array.
MOVE_CUBE = [CubieCube() for i in range(6)]

MOVE_CUBE[0].cp = _cpU
MOVE_CUBE[0].co = _coU
MOVE_CUBE[0].ep = _epU
MOVE_CUBE[0].eo = _eoU

MOVE_CUBE[1].cp = _cpR
MOVE_CUBE[1].co = _coR
MOVE_CUBE[1].ep = _epR
MOVE_CUBE[1].eo = _eoR

MOVE_CUBE[2].cp = _cpF
MOVE_CUBE[2].co = _coF
MOVE_CUBE[2].ep = _epF
MOVE_CUBE[2].eo = _eoF

MOVE_CUBE[3].cp = _cpD
MOVE_CUBE[3].co = _coD
MOVE_CUBE[3].ep = _epD
MOVE_CUBE[3].eo = _eoD

MOVE_CUBE[4].cp = _cpL
MOVE_CUBE[4].co = _coL
MOVE_CUBE[4].ep = _epL
MOVE_CUBE[4].eo = _eoL

MOVE_CUBE[5].cp = _cpB
MOVE_CUBE[5].co = _coB
MOVE_CUBE[5].ep = _epB
MOVE_CUBE[5].eo = _eoB
