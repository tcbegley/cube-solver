"""
We enumerate the colors and provide a dictionary for lookup of each color.
"""

U, R, F, D, L, B = range(6)

# Create two way lookup of strings / indices
COLORS = {
    **dict(zip(("U", "R", "F", "D", "L", "B"), range(6))),
    **dict(zip(range(6), ("U", "R", "F", "D", "L", "B")))
}
