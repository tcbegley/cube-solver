import math

from twophase.pieces import Move

TWIST_MAX = 3**7
FLIP_MAX = 2**11
UD_SLICE_MAX = math.comb(12, 4)
EDGE4_MAX = 24
EDGE8_MAX = 40_320
CORNER_MAX = 40_320

MOVES = 18
SYMMETRIES = 48
SYMMETRIES_D4H = 16
FLIP_UD_SLICE_CLASSES = 64430
CORNER_CLASSES = 2768

PHASE_1_MOVES = [
    Move.U1,
    Move.U2,
    Move.U3,
    Move.R1,
    Move.R2,
    Move.R3,
    Move.F1,
    Move.F2,
    Move.F3,
    Move.D1,
    Move.D2,
    Move.D3,
    Move.L1,
    Move.L2,
    Move.L3,
    Move.B1,
    Move.B2,
    Move.B3,
]
PHASE_2_PRUNE_UNFILLED_DEPTH = 11

PHASE_2_MOVES = [
    Move.U1,
    Move.U2,
    Move.U3,
    Move.R2,
    Move.F2,
    Move.D1,
    Move.D2,
    Move.D3,
    Move.L2,
    Move.B2,
]
