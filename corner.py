"""
We enumerate the corner pieces and provide a dictionary for lookup of the
pieces.
"""

URF, UFL, ULB, UBR, DFR, DLF, DBL, DRB = range(8)

CORNERS = dict(
    zip(
        ("URF", "UFL", "ULB", "UBR", "DFR", "DLF", "DBL", "DRB"),
        range(8)
    )
)
