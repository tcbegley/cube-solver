from . import color, cubie_cube, facelet

# Maps corner positions to facelet positions
corner_facelet = (
    (facelet.U9, facelet.R1, facelet.F3),
    (facelet.U7, facelet.F1, facelet.L3),
    (facelet.U1, facelet.L1, facelet.B3),
    (facelet.U3, facelet.B1, facelet.R3),
    (facelet.D3, facelet.F9, facelet.R7),
    (facelet.D1, facelet.L9, facelet.F7),
    (facelet.D7, facelet.B9, facelet.L7),
    (facelet.D9, facelet.R9, facelet.B7)
)

# Maps edge positions to facelet positions
edge_facelet = (
    (facelet.U6, facelet.R2), (facelet.U8, facelet.F2),
    (facelet.U4, facelet.L2), (facelet.U2, facelet.B2),
    (facelet.D6, facelet.R8), (facelet.D2, facelet.F8),
    (facelet.D4, facelet.L8), (facelet.D8, facelet.B8),
    (facelet.F6, facelet.R4), (facelet.F4, facelet.L6),
    (facelet.B6, facelet.L4), (facelet.B4, facelet.R6)
)

# Maps corner positions to colours
corner_color = (
    (color.U, color.R, color.F), (color.U, color.F, color.L),
    (color.U, color.L, color.B), (color.U, color.B, color.R),
    (color.D, color.F, color.R), (color.D, color.L, color.F),
    (color.D, color.B, color.L), (color.D, color.R, color.B)
)

# Maps edge positions to colours
edge_color = (
    (color.U, color.R), (color.U, color.F), (color.U, color.L),
    (color.U, color.B), (color.D, color.R), (color.D, color.F),
    (color.D, color.L), (color.D, color.B), (color.F, color.R),
    (color.F, color.L), (color.B, color.L), (color.B, color.R)
)


class FaceCube:
    def __init__(self, cube_string=''.join(c * 9 for c in "URFDLB")):
        """
        Initialise FaceCube from cube_string, if cube_string is not provided we
        initialise a clean cube.
        """
        self.f = [0] * 54
        for i in range(54):
            self.f[i] = color.COLORS[cube_string[i]]

    def to_string(self):
        """Convert facecube to cubestring"""
        return ''.join(color.COLORS[i] for i in self.f)

    def to_cubiecube(self):
        """Convert FaceCube to CubieCube"""
        cc = cubie_cube.CubieCube()
        for i in range(8):
            # all corner names start with U or D, allowing us to find
            # orientation of any given corner as follows
            for ori in range(3):
                if self.f[corner_facelet[i][ori]] in [color.U, color.D]:
                    break
            color1 = self.f[corner_facelet[i][(ori + 1) % 3]]
            color2 = self.f[corner_facelet[i][(ori + 2) % 3]]
            for j in range(8):
                if (color1 == corner_color[j][1] and
                        color2 == corner_color[j][2]):
                    cc.cp[i] = j
                    cc.co[i] = ori
                    break

        for i in range(12):
            for j in range(12):
                if (self.f[edge_facelet[i][0]] == edge_color[j][0] and
                        self.f[edge_facelet[i][1]] == edge_color[j][1]):
                    cc.ep[i] = j
                    cc.eo[i] = 0
                    break
                if (self.f[edge_facelet[i][0]] == edge_color[j][1] and
                        self.f[edge_facelet[i][1]] == edge_color[j][0]):
                    cc.ep[i] = j
                    cc.eo[i] = 1
                    break
        return cc
