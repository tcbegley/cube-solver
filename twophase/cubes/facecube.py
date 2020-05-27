from ..pieces import Color, Facelet
from . import cubiecube

# Maps corner positions to facelet positions
corner_facelet = (
    (Facelet.U9, Facelet.R1, Facelet.F3),
    (Facelet.U7, Facelet.F1, Facelet.L3),
    (Facelet.U1, Facelet.L1, Facelet.B3),
    (Facelet.U3, Facelet.B1, Facelet.R3),
    (Facelet.D3, Facelet.F9, Facelet.R7),
    (Facelet.D1, Facelet.L9, Facelet.F7),
    (Facelet.D7, Facelet.B9, Facelet.L7),
    (Facelet.D9, Facelet.R9, Facelet.B7),
)

# Maps edge positions to facelet positions
edge_facelet = (
    (Facelet.U6, Facelet.R2),
    (Facelet.U8, Facelet.F2),
    (Facelet.U4, Facelet.L2),
    (Facelet.U2, Facelet.B2),
    (Facelet.D6, Facelet.R8),
    (Facelet.D2, Facelet.F8),
    (Facelet.D4, Facelet.L8),
    (Facelet.D8, Facelet.B8),
    (Facelet.F6, Facelet.R4),
    (Facelet.F4, Facelet.L6),
    (Facelet.B6, Facelet.L4),
    (Facelet.B4, Facelet.R6),
)

# Maps corner positions to colours
corner_color = (
    (Color.U, Color.R, Color.F),
    (Color.U, Color.F, Color.L),
    (Color.U, Color.L, Color.B),
    (Color.U, Color.B, Color.R),
    (Color.D, Color.F, Color.R),
    (Color.D, Color.L, Color.F),
    (Color.D, Color.B, Color.L),
    (Color.D, Color.R, Color.B),
)

# Maps edge positions to colours
edge_color = (
    (Color.U, Color.R),
    (Color.U, Color.F),
    (Color.U, Color.L),
    (Color.U, Color.B),
    (Color.D, Color.R),
    (Color.D, Color.F),
    (Color.D, Color.L),
    (Color.D, Color.B),
    (Color.F, Color.R),
    (Color.F, Color.L),
    (Color.B, Color.L),
    (Color.B, Color.R),
)


class FaceCube:
    def __init__(self, cube_string="".join(c * 9 for c in "URFDLB")):
        """
        Initialise FaceCube from cube_string, if cube_string is not provided we
        initialise a clean cube.
        """
        self.f = [0] * 54
        for i in range(54):
            self.f[i] = Color[cube_string[i]]

    def to_string(self):
        """Convert facecube to cubestring"""
        return "".join(Color(i).name for i in self.f)

    def to_cubiecube(self):
        """Convert FaceCube to CubieCube"""
        cc = cubiecube.CubieCube()
        for i in range(8):
            # all corner names start with U or D, allowing us to find
            # orientation of any given corner as follows
            for ori in range(3):
                if self.f[corner_facelet[i][ori]] in [Color.U, Color.D]:
                    break
            color1 = self.f[corner_facelet[i][(ori + 1) % 3]]
            color2 = self.f[corner_facelet[i][(ori + 2) % 3]]
            for j in range(8):
                if (
                    color1 == corner_color[j][1]
                    and color2 == corner_color[j][2]
                ):
                    cc.cp[i] = j
                    cc.co[i] = ori
                    break

        for i in range(12):
            for j in range(12):
                if (
                    self.f[edge_facelet[i][0]] == edge_color[j][0]
                    and self.f[edge_facelet[i][1]] == edge_color[j][1]
                ):
                    cc.ep[i] = j
                    cc.eo[i] = 0
                    break
                if (
                    self.f[edge_facelet[i][0]] == edge_color[j][1]
                    and self.f[edge_facelet[i][1]] == edge_color[j][0]
                ):
                    cc.ep[i] = j
                    cc.eo[i] = 1
                    break
        return cc
