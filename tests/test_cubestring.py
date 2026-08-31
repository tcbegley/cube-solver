import pytest

from twophase.cubestring import parse
from twophase.exceptions import InvalidCube
from twophase.pieces import Corner, Edge
from twophase.tables.cubiecube import CubieCube

SOLVED_STRING = "UUUUUUUUURRRRRRRRRFFFFFFFFFDDDDDDDDDLLLLLLLLLBBBBBBBBB"


class TestSolvedCube:
    def test_parse_solved(self):
        cc = parse(SOLVED_STRING)
        assert cc == CubieCube()

    def test_case_insensitive(self):
        cc = parse(SOLVED_STRING.lower())
        assert cc == CubieCube()


class TestScrambledCubes:
    def test_single_move_u(self):
        """U move cycles four corners and four edges on the U face."""
        cc = parse("UUUUUUUUUBBBRRRRRRRRRFFFFFFDDDDDDDDDFFFLLLLLLLLLBBBBBB")
        # corners: URF→UBR→ULB→UFL (cycle of 4)
        assert cc.cp == (
            Corner.UBR,
            Corner.URF,
            Corner.UFL,
            Corner.ULB,
            Corner.DFR,
            Corner.DLF,
            Corner.DBL,
            Corner.DRB,
        )
        # U moves don't twist corners
        assert cc.co == (0, 0, 0, 0, 0, 0, 0, 0)
        # edges: UR→UB→UL→UF (cycle of 4)
        assert cc.ep == (
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
        # U moves don't flip edges
        assert cc.eo == (0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)

    def test_r2_u_l(self):
        """R2 U L scramble from the debug notebook."""
        cc = parse("BUUBUULDDFBBRRRRRRURRUFBDFBRDUFDUFDULLFLLFLLBLLDFBDFBD")
        assert cc.twist == 412
        assert cc.flip == 0
        assert cc.corner == 36781

    def test_complex_scramble(self):
        """A fully scrambled cube should parse and verify successfully."""
        cc = parse("BUFDUFDLLBLDBRLFDBLDURFRBUULFLLDBRURRFFRLFUUDRRUBBDDBF")
        # just check it parses and produces a valid cube (verify is called
        # internally by parse)
        assert cc is not None


class TestValidation:
    def test_wrong_length(self):
        with pytest.raises(InvalidCube, match="54 characters"):
            parse("UUUUUU")

    def test_invalid_character(self):
        with pytest.raises(InvalidCube, match="invalid character"):
            parse("X" + SOLVED_STRING[1:])

    def test_wrong_colour_count(self):
        # replace one U with an R (10 R's, 8 U's)
        bad = "RUUUUUUUURRRRRRRRRFFFFFFFFFDDDDDDDDDLLLLLLLLLBBBBBBBBB"
        with pytest.raises(InvalidCube, match="exactly 9 times"):
            parse(bad)

    def test_impossible_twist(self):
        """A single twisted corner is not solvable."""
        # swap two facelets of the URF corner to create an impossible twist
        with pytest.raises(InvalidCube):
            parse("UUUUUUUURRRRRRRRRFUFFFFFFFDDDDDDDDDBLLLLLLLLBBBBBBBBB")

    def test_swapped_edges(self):
        """A single edge swap is not solvable (parity error)."""
        # swap UR and UF edges: put F colour where R should be on U face
        with pytest.raises(InvalidCube):
            parse("UUUUUFUURFRRRRRRRUFFFFFFFDDDDDDDDDDLLLLLLLLLBBBBBBBBB")
