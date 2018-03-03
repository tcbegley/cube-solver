"""
This class describes cubes on the level of the cubies.
"""
import corner
import edge
import face_cube


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
cpU = (corner.UBR, corner.URF, corner.UFL, corner.ULB,
       corner.DFR, corner.DLF, corner.DBL, corner.DRB)
coU = (0, 0, 0, 0, 0, 0, 0, 0)
epU = (edge.UB, edge.UR, edge.UF, edge.UL, edge.DR, edge.DF,
       edge.DL, edge.DB, edge.FR, edge.FL, edge.BL, edge.BR)
eoU = (0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)

cpR = (corner.DFR, corner.UFL, corner.ULB, corner.URF,
       corner.DRB, corner.DLF, corner.DBL, corner.UBR)
coR = (2, 0, 0, 1, 1, 0, 0, 2)
epR = (edge.FR, edge.UF, edge.UL, edge.UB, edge.BR, edge.DF,
       edge.DL, edge.DB, edge.DR, edge.FL, edge.BL, edge.UR)
eoR = (0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)

cpF = (corner.UFL, corner.DLF, corner.ULB, corner.UBR,
       corner.URF, corner.DFR, corner.DBL, corner.DRB)
coF = (1, 2, 0, 0, 2, 1, 0, 0)
epF = (edge.UR, edge.FL, edge.UL, edge.UB, edge.DR, edge.FR,
       edge.DL, edge.DB, edge.UF, edge.DF, edge.BL, edge.BR)
eoF = (0, 1, 0, 0, 0, 1, 0, 0, 1, 1, 0, 0)

cpD = (corner.URF, corner.UFL, corner.ULB, corner.UBR,
       corner.DLF, corner.DBL, corner.DRB, corner.DFR)
coD = (0, 0, 0, 0, 0, 0, 0, 0)
epD = (edge.UR, edge.UF, edge.UL, edge.UB, edge.DF, edge.DL,
       edge.DB, edge.DR, edge.FR, edge.FL, edge.BL, edge.BR)
eoD = (0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)

cpL = (corner.URF, corner.ULB, corner.DBL, corner.UBR,
       corner.DFR, corner.UFL, corner.DLF, corner.DRB)
coL = (0, 1, 2, 0, 0, 2, 1, 0)
epL = (edge.UR, edge.UF, edge.BL, edge.UB, edge.DR, edge.DF,
       edge.FL, edge.DB, edge.FR, edge.UL, edge.DL, edge.BR)
eoL = (0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)

cpB = (corner.URF, corner.UFL, corner.UBR, corner.DRB,
       corner.DFR, corner.DLF, corner.ULB, corner.DBL)
coB = (0, 0, 1, 2, 0, 0, 2, 1)
epB = (edge.UR, edge.UF, edge.UL, edge.BR, edge.DR, edge.DF,
       edge.DL, edge.BL, edge.FR, edge.FL, edge.UB, edge.DB)
eoB = (0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 1, 1)


class CubieCube:
    def __init__(self, cp=None, co=None, ep=None, eo=None):
        # Initialise clean cube if position not given.
        if cp and co and ep and eo:
            self.cp = cp[:]
            self.co = co[:]
            self.ep = ep[:]
            self.eo = eo[:]
        else:
            self.cp = [corner.URF, corner.UFL, corner.ULB, corner.UBR,
                       corner.DFR, corner.DLF, corner.DBL, corner.DRB]
            self.co = [0, 0, 0, 0, 0, 0, 0, 0]
            self.ep = [edge.UR, edge.UF, edge.UL, edge.UB, edge.DR, edge.DF,
                       edge.DL, edge.DB, edge.FR, edge.FL, edge.BL, edge.BR]
            self.eo = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]

    def corner_multiply(self, b):
        # compute resulting permutation and orientation or corners if applying
        # sequence of permutations b to current cube. The rules, using the
        # replaced by notation are (for example using the sequence F then R)
        # (F*R)[UBR].c = F[R[UBR].c].c (i.e. the corner UBR is replaced by the
        # corner at position R[UBR].c, and this corner is whatever F left there
        # For the orientation we have
        # (F*R)[UBR].o = F[R[UBR].c].o + R[UBR].o (i.e. the orientation is
        # change in orientation due to F (first term plus the change due to R
        corner_perm = [self.cp[b.cp[i]] for i in range(8)]
        corner_ori = [(self.co[b.cp[i]] + b.co[i]) % 3 for i in range(8)]
        self.co = corner_ori[:]
        self.cp = corner_perm[:]

    def edge_multiply(self, b):
        # Same as the corner_multiply function, but for the edges.
        edge_perm = [self.ep[b.ep[i]] for i in range(12)]
        edge_ori = [(self.eo[b.ep[i]] + b.eo[i]) % 2 for i in range(12)]
        self.eo = edge_ori[:]
        self.ep = edge_perm[:]

    def multiply(self, b):
        self.corner_multiply(b)
        self.edge_multiply(b)

    def inverse_cubiecube(self, cube):
        # computes the inverse cube
        for e in range(12):
            cube.ep[self.ep[e]] = e
        for e in range(12):
            cube.eo[e] = self.eo[cube.ep[e]]
        for c in range(8):
            cube.cp[self.cp[c]] = c
        for c in range(8):
            ori = self.co[cube.cp[c]]
            cube.co[c] = (-ori) % 3

    # convert cubiecube to facecube
    def to_facecube(self):
        # use look-up tables in facecube to get colours of the facelets from
        # cubiecube representation.
        ret = face_cube.FaceCube()
        for i in range(8):
            j = self.cp[i]
            ori = self.co[i]
            for k in range(3):
                ret.f[
                    face_cube.corner_facelet[i][(k + ori) % 3]
                ] = face_cube.corner_color[j][k]
        for i in range(12):
            j = self.ep[i]
            ori = self.eo[i]
            for k in range(2):
                facelet_index = face_cube.edge_facelet[i][(k + ori) % 2]
                ret.f[facelet_index] = face_cube.edge_color[j][k]
        return ret

    def corner_parity(self):
        # parity of the corner permutation.
        s = 0
        for i in range(7, 0, -1):
            for j in range(i - 1, - 1, -1):
                if self.cp[j] > self.cp[i]:
                    s += 1
        return s % 2

    def edge_parity(self):
        # parity of the edge permutation. cube is solvable iff this matches corner parity
        s = 0
        for i in range(11, 0, -1):
            for j in range(i - 1, - 1, -1):
                if self.ep[j] > self.ep[i]:
                    s += 1
        return s % 2

    # ----------   Phase 1 Coordinates  ---------- #
    def get_twist(self):
        # compute the corner orientation coordinate
        # 0 <= ret < 3^7
        ret = 0
        for i in range(7):
            ret = 3 * ret + self.co[i]
        return ret

    def set_twist(self, twist):
        # compute corner orientations from twist coordinate.
        # sum is used to find orientation of 8th corner (orientations sum to multiple of 3)
        sum = 0
        for i in range(7):
            x = twist % 3
            self.co[6 - i] = x
            sum += x
            twist /= 3
        self.co[7] = (-sum) % 3

    def get_flip(self):
        # compute the edge flip coordinate
        # 0 <= ret < 2^11
        ret = 0
        for i in range(11):
            ret = 2 * ret + self.eo[i]
        return ret

    def set_flip(self, flip):
        # compute edge flips from flip coordinate
        # sum is used to find flip of 12th edge (flips sum to a multiple of 2)
        sum = 0
        for i in range(11):
            x = flip % 2
            self.eo[10 - i] = x
            sum += x
            flip /= 2
        self.eo[11] = (-sum) % 2

    def get_slice(self):
        # describes the position (but not order) of the 4 edges FR, FL, BL, BR
        # 0 <= ret < 12C4
        ret, s = 0, 0
        for j in range(12):
            if 8 <= self.ep[j] < 12:
                s += 1
            elif s >= 1:
                ret += choose(j, s - 1)
        return ret

    def set_slice(self, udslice):
        # computes positions (but not order) of the 4 edges FR, FL, BL, BR
        slice_edge = [edge.FR, edge.FL, edge.BL, edge.BR]
        other_edge = [edge.UR, edge.UF, edge.UL,
                      edge.UB, edge.DR, edge.DF, edge.DL, edge.DB]
        # invalidate edges
        for i in range(12):
            self.ep[i] = edge.DB
        # we first position the slice edges
        s = 3
        for j in range(11, -1, -1):
            if udslice - choose(j, s) < 0:
                self.ep[j] = slice_edge[s]
                s -= 1
            else:
                udslice -= choose(j, s)
        # then the remaining edges
        x = 0
        for j in range(12):
            if self.ep[j] == edge.DB:
                self.ep[j] = other_edge[x]
                x += 1

    ########################   Phase 2 Coordinates   ########################

    def get_edge4(self):
        # coordinate describing permutation of the 4 edges FR, FL, BL, BR.
        # takes values in range 0, ..., 23 (24 = 4! possibilities)
        edge4 = self.ep[8:]
        ret = 0
        for j in range(3, 0, -1):
            s = 0
            for i in range(j):
                if edge4[i] > edge4[j]:
                    s += 1
            ret = j * (ret + s)
        return ret

    def set_edge4(self, edge4):
        # computes permutation of the 4 edges FR, FL, BL, BR from the coordinate edge4
        # only valid in phase 2
        sliceedge = [edge.FR, edge.FL, edge.BL, edge.BR]
        coeffs = [0] * 3
        for i in range(1, 4):
            coeffs[i - 1] = edge4 % (i + 1)
            edge4 /= (i + 1)
        perm = [0] * 4
        for i in range(2, -1, -1):
            perm[i + 1] = sliceedge.pop(i + 1 - coeffs[i])
        perm[0] = sliceedge[0]
        self.ep[8:] = perm[:]

    def get_edge8(self):
        # coordinate describing permutation of the 8 edge pieces UR, UF, UL, UB, DR, DF, DL, DB in the U and D faces
        # only valid in phase 2
        # permutation of the first 8 piece (valid only in phase 2)
        # 0 <= ret < 8!
        ret = 0
        for j in range(7, 0, -1):
            s = 0
            for i in range(j):
                if self.ep[i] > self.ep[j]:
                    s += 1
            ret = j * (ret + s)
        return ret

    def set_edge8(self, edge8):
        # compute permutation of the 8 edge pieces UR, UF, UL, UB, DR, DF, DL, DB in the U and D faces
        # only valid in phase 2
        edges = range(8)
        perm = [0] * 8
        coeffs = [0] * 7
        for i in range(1, 8):
            coeffs[i - 1] = edge8 % (i + 1)
            edge8 /= (i + 1)
        for i in range(6, -1, -1):
            perm[i + 1] = edges.pop(i + 1 - coeffs[i])
        perm[0] = edges[0]
        self.ep[:8] = perm[:]

    def get_corner(self):
        # compute the corner permutation coordinate
        # 0 <= ret < 8!
        ret = 0
        for j in range(7, 0, -1):
            s = 0
            for i in range(j):
                if self.cp[i] > self.cp[j]:
                    s += 1
            ret = j * (ret + s)
        return ret

    def set_corner(self, idx):
        # compute corner permutation from coordinate
        corners = range(8)
        perm = [0] * 8
        coeffs = [0] * 7
        for i in range(1, 8):
            coeffs[i - 1] = idx % (i + 1)
            idx /= (i + 1)
        for i in range(6, -1, -1):
            perm[i + 1] = corners.pop(i + 1 - coeffs[i])
        perm[0] = corners[0]
        self.cp = perm[:]

    ################ Misc. Coordinates ################

    # edge permutation coordinate not used in solving, but needed to generate random cubes
    def get_edge(self):
        # compute the edge permutation coordinate
        # 0 <= ret < 12!
        ret = 0
        for j in range(11, 0, -1):
            s = 0
            for i in range(j):
                if self.ep[i] > self.ep[j]:
                    s += 1
            ret = j * (ret + s)
        return ret

    def set_edge(self, idx):
        # compute edge permutation from coordinate
        edges = range(12)
        perm = [0] * 12
        coeffs = [0] * 11
        for i in range(1, 12):
            coeffs[i - 1] = idx % (i + 1)
            idx /= (i + 1)
        for i in range(10, -1, -1):
            perm[i + 1] = edges.pop(i + 1 - coeffs[i])
        perm[0] = edges[0]
        self.ep = perm[:]

    ################ Solvability Check ################

    # Check a cubiecube for solvability
    # 0: Solvable
    # -2: not all 12 edges exist exactly once
    # -3: flip error: one edge should be flipped
    # -4: not all corners exist exactly once
    # -5: twist error - a corner must be twisted
    # -6: Parity error - two corners or edges have to be exchanged
    def verify(self):
        sum = 0
        edge_count = [0 for i in range(12)]
        for e in range(12):
            edge_count[self.ep[e]] += 1
        for i in range(12):
            if edge_count[i] != 1:
                return -2
        for i in range(12):
            sum += self.eo[i]
        if sum % 2 != 0:
            return -3
        corner_count = [0] * 8
        for c in range(8):
            corner_count[self.cp[c]] += 1
        for i in range(8):
            if corner_count[i] != 1:
                return -4
        sum = 0
        for i in range(8):
            sum += self.co[i]
        if sum % 3 != 0:
            return -5
        if self.edge_parity() != self.corner_parity():
            return -6
        return 0


# we store the six possible clockwise 1/4 turn moves in the following array.
MOVE_CUBE = [CubieCube() for i in range(6)]
MOVE_CUBE[0].cp = cpU
MOVE_CUBE[0].co = coU
MOVE_CUBE[0].ep = epU
MOVE_CUBE[0].eo = eoU
MOVE_CUBE[1].cp = cpR
MOVE_CUBE[1].co = coR
MOVE_CUBE[1].ep = epR
MOVE_CUBE[1].eo = eoR
MOVE_CUBE[2].cp = cpF
MOVE_CUBE[2].co = coF
MOVE_CUBE[2].ep = epF
MOVE_CUBE[2].eo = eoF
MOVE_CUBE[3].cp = cpD
MOVE_CUBE[3].co = coD
MOVE_CUBE[3].ep = epD
MOVE_CUBE[3].eo = eoD
MOVE_CUBE[4].cp = cpL
MOVE_CUBE[4].co = coL
MOVE_CUBE[4].ep = epL
MOVE_CUBE[4].eo = eoL
MOVE_CUBE[5].cp = cpB
MOVE_CUBE[5].co = coB
MOVE_CUBE[5].ep = epB
MOVE_CUBE[5].eo = eoB
