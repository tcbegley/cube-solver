"""
We enumerate the edge pieces and provide a dictionary for lookup of the
pieces.
"""

UR, UF, UL, UB, DR, DF, DL, DB, FR, FL, BL, BR = range(12)

EDGES = dict(
    zip(
        ("UR", "UF", "UL", "UB", "DR", "DF",
         "DL", "DB", "FR", "FL", "BL", "BR"),
        range(12)
    )
)
