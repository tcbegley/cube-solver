from __future__ import annotations

from typing import overload

from twophase.pieces import Corner, Edge
from twophase.tables.cubiecube import CubieCube

# 120 degree clockwise rotation around the long diagonal URF-DBL
ROT_URF_120 = CubieCube(
    cp=(
        Corner.URF,
        Corner.DFR,
        Corner.DLF,
        Corner.UFL,
        Corner.UBR,
        Corner.DRB,
        Corner.DBL,
        Corner.ULB,
    ),
    co=(1, 2, 1, 2, 2, 1, 2, 1),
    ep=(
        Edge.UF,
        Edge.FR,
        Edge.DF,
        Edge.FL,
        Edge.UB,
        Edge.BR,
        Edge.DB,
        Edge.BL,
        Edge.UR,
        Edge.DR,
        Edge.DL,
        Edge.UL,
    ),
    eo=(1, 0, 1, 0, 1, 0, 1, 0, 1, 1, 1, 1),
)

# 180° rotation around the axis through the F and B centers
ROT_F_180 = CubieCube(
    cp=(
        Corner.DLF,
        Corner.DFR,
        Corner.DRB,
        Corner.DBL,
        Corner.UFL,
        Corner.URF,
        Corner.UBR,
        Corner.ULB,
    ),
    co=(0, 0, 0, 0, 0, 0, 0, 0),
    ep=(
        Edge.DL,
        Edge.DF,
        Edge.DR,
        Edge.DB,
        Edge.UL,
        Edge.UF,
        Edge.UR,
        Edge.UB,
        Edge.FL,
        Edge.FR,
        Edge.BR,
        Edge.BL,
    ),
    eo=(0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
)

# 90° clockwise rotation around the axis through the U and D centers
ROT_U_90 = CubieCube(
    cp=(
        Corner.UBR,
        Corner.URF,
        Corner.UFL,
        Corner.ULB,
        Corner.DRB,
        Corner.DFR,
        Corner.DLF,
        Corner.DBL,
    ),
    co=(0, 0, 0, 0, 0, 0, 0, 0),
    ep=(
        Edge.UB,
        Edge.UR,
        Edge.UF,
        Edge.UL,
        Edge.DB,
        Edge.DR,
        Edge.DF,
        Edge.DL,
        Edge.BR,
        Edge.FR,
        Edge.FL,
        Edge.BL,
    ),
    eo=(0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1),
)

# reflection in M slice (the plane through the U, D, F, B centers)
REF_M = CubieCube(
    cp=(
        Corner.UFL,
        Corner.URF,
        Corner.UBR,
        Corner.ULB,
        Corner.DLF,
        Corner.DFR,
        Corner.DRB,
        Corner.DBL,
    ),
    co=(3, 3, 3, 3, 3, 3, 3, 3),
    ep=(
        Edge.UL,
        Edge.UF,
        Edge.UR,
        Edge.UB,
        Edge.DL,
        Edge.DF,
        Edge.DR,
        Edge.DB,
        Edge.FL,
        Edge.FR,
        Edge.BR,
        Edge.BL,
    ),
    eo=(0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
)


class Symmetries:
    _symmetries: list[CubieCube] = []
    _inverse_symmetries: list[CubieCube] = []

    def __new__(cls, subgroup=False):
        if not cls._symmetries:
            # populate list of symmetries
            cube = CubieCube()
            for _urf_rot in range(3):
                for _f_rot in range(2):
                    for _u_rot in range(4):
                        for _m_ref in range(2):
                            cls._symmetries.append(cube)
                            cube *= REF_M
                        cube *= ROT_U_90
                    cube *= ROT_F_180
                cube *= ROT_URF_120

            cls._inverse_symmetries = []
            for sym in cls._symmetries:
                for inv_candidate in cls._symmetries:
                    result = sym.corner_multiply(inv_candidate)
                    if (
                        result.cp[Corner.URF] == Corner.URF
                        and result.cp[Corner.UFL] == Corner.UFL
                        and result.cp[Corner.ULB] == Corner.ULB
                    ):
                        # location of these three corners is enough to determine inverse
                        cls._inverse_symmetries.append(inv_candidate)
                        break

        return super().__new__(cls)

    def __init__(self, subgroup=False):
        self._lim = 16 if subgroup else 48

    @overload
    def __getitem__(self, idx: int) -> CubieCube: ...

    @overload
    def __getitem__(self, idx: slice) -> list[CubieCube]: ...

    def __getitem__(self, idx: int | slice) -> CubieCube | list[CubieCube]:
        return self._symmetries[: self._lim][idx]

    def __iter__(self):
        return iter(self._symmetries[: self._lim])

    def __len__(self) -> int:
        return self._lim

    @property
    def inverse(self) -> list[CubieCube]:
        return self._inverse_symmetries[: self._lim]


def cube_symmetries(cube: CubieCube) -> list[int]:
    symmetries = Symmetries()
    n_sym = len(symmetries)
    s = []
    for i, sym in enumerate(symmetries):
        cube2 = sym * cube * symmetries.inverse[i]
        if cube == cube2:
            s.append(i)
        cube2 = cube2.invert()
        if cube == cube2:
            s.append(i + n_sym)
    return s
