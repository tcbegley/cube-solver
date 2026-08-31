"""Immutable coordinate states used by the two search phases."""

from typing import NamedTuple


class Phase1State(NamedTuple):
    """Coordinates needed to search phase 1 and transition into phase 2."""

    # Coordinates that define phase 1 membership.
    twist: int
    flip: int
    ud_slice_sorted: int

    # Coordinates carried along so phase 2 can start without replaying moves.
    u_edges_sorted: int
    d_edges_sorted: int
    corner: int


class Phase2State(NamedTuple):
    """Coordinates needed to search phase 2."""

    edge4: int
    edge8: int
    corner: int
