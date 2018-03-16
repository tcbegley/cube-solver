"""
We enumerate the edge pieces and provide a dictionary for lookup of the
pieces.
"""

UR, UF, UL, UB, DR, DF, DL, DB, FR, FL, BL, BR = range(12)

# Create two way lookup of strings / indices
EDGES = {
    **dict(zip(
        ("UR", "UF", "UL", "UB", "DR", "DF",
         "DL", "DB", "FR", "FL", "BL", "BR"),
        range(12)
    )),
    **dict(zip(
        range(12),
        ("UR", "UF", "UL", "UB", "DR", "DF",
         "DL", "DB", "FR", "FL", "BL", "BR")
    ))
}
