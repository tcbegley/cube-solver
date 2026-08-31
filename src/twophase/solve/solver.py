"""
Two-phase Rubik's cube solver using Kociemba's algorithm.

The implementation separates three concerns:

- :class:`Solver` is a thread-safe facade over the read-only lookup tables.
- :class:`_CoordinateModel` contains pure coordinate transitions and heuristics.
- :class:`_SearchPortfolio` coordinates symmetry-equivalent searches.
- :class:`_SearchSession` owns the mutable state for one search tree.

The search uses IDA* in two phases. Phase 1 reduces the cube to the G1 subgroup;
phase 2 solves it using only moves that preserve G1. Progressive searches continue
after finding a solution, using its length as the bound for subsequent searches.
"""

import time
from collections.abc import Generator
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from queue import Queue
from threading import Event

from twophase.constants import (
    EDGE4_MAX,
    EDGE8_MAX,
    FLIP_MAX,
    MOVES,
    PHASE_1_MOVES,
    PHASE_2_MOVES,
    PHASE_2_PRUNE_UNFILLED_DEPTH,
    SYMMETRIES_D4H,
    TWIST_MAX,
)
from twophase.pieces import Move
from twophase.solve.state import Phase1State, Phase2State
from twophase.tables.cubiecube import CubieCube
from twophase.tables.symmetries import Symmetries
from twophase.tables.tables import Tables, make_or_load_tables

# Phase 2 searches at most this many moves deep. Optimal phase 2 solutions rarely
# exceed 10 moves.
MAX_PHASE2_DEPTH = 11

# When phase 1 is already in G1 and nearly out of budget, phase 2 moves are deferred
# to the dedicated phase 2 search.
_PHASE_1_DEFERRED_MOVES = tuple(
    move for move in PHASE_1_MOVES if move not in PHASE_2_MOVES
)

# Calling time.monotonic() at every node is expensive.
_TIMEOUT_CHECK_INTERVAL = 10_000

# Conjugating by these symmetries views the cube with each of the U, R, and F
# directions as the phase 1 U/D axis. Searching their inverses gives six distinct
# orderings of the same solution space.
_SEARCH_SYMMETRIES = (0, 16, 32)


def _make_successor_table(moves: tuple[int, ...]) -> tuple[tuple[int, ...], ...]:
    """Precompute non-redundant moves for each possible previous move."""
    return tuple(
        tuple(move for move in moves if move // 3 - previous_move // 3 not in (0, 3))
        for previous_move in range(MOVES)
    )


_PHASE_1_ROOT_MOVES = tuple(PHASE_1_MOVES)
_PHASE_2_ROOT_MOVES = tuple(PHASE_2_MOVES)
_PHASE_1_SUCCESSORS = _make_successor_table(_PHASE_1_ROOT_MOVES)
_PHASE_1_DEFERRED_SUCCESSORS = _make_successor_table(_PHASE_1_DEFERRED_MOVES)
_PHASE_2_SUCCESSORS = _make_successor_table(_PHASE_2_ROOT_MOVES)


@dataclass(frozen=True, slots=True)
class _SearchVariant:
    cube: CubieCube
    symmetry_index: int
    inverted: bool


@dataclass(frozen=True, slots=True)
class _WorkerDone:
    error: BaseException | None = None


class Solver:
    """
    Kociemba two-phase solver with progressive solution shortening.

    A solver owns only the read-only coordinate model that is shared by its searches.
    Each call creates a search session for its mutable path and control state, so one
    solver may safely service concurrent calls. The search is CPU-bound, however, so
    parallel speedups may require processes or a free-threaded Python runtime.
    """

    def __init__(self, cache_path: str | Path | None = None) -> None:
        tables = make_or_load_tables(cache_path)
        self._coordinates = _CoordinateModel(tables)

    def solve(
        self, cube: CubieCube, max_length: int = 20, timeout: float = float("inf")
    ) -> list[Move] | None:
        """
        Find a solution and return it immediately.

        ``max_length`` is an inclusive upper bound. ``None`` is returned if no
        solution is found within that bound before the timeout.
        """
        return _SearchPortfolio(
            self._coordinates, cube, max_length, timeout
        ).first_solution()

    def solve_progressively(
        self, cube: CubieCube, max_length: int = 20, timeout: float = 10.0
    ) -> Generator[list[Move]]:
        """
        Yield shorter solutions until the search is exhausted or times out.

        Independent workers search rotated and inverted views of the cube. Results are
        transformed back to the original orientation and merged here so that yielded
        lengths remain strictly decreasing.
        """
        yield from _SearchPortfolio(
            self._coordinates, cube, max_length, timeout
        ).progressive_solutions()


class _CoordinateModel:
    """
    Read-only coordinate transitions and pruning heuristics.

    Methods on this class are deterministic functions of their arguments and the
    injected lookup tables. Keeping resource loading outside the model makes that
    dependency explicit, while keeping coordinate details out of the search control
    flow.
    """

    def __init__(self, tables: Tables) -> None:
        self.tables = tables
        self.symmetries = Symmetries()
        self.inverse_symmetry_indices = tuple(
            next(
                i for i, candidate in enumerate(self.symmetries) if candidate == inverse
            )
            for inverse in self.symmetries.inverse
        )

    def search_variants(self, cube: CubieCube) -> list[_SearchVariant]:
        """Return distinct rotated views of the cube and its inverse."""
        variants: list[_SearchVariant] = []
        for inverted in (False, True):
            source = cube.invert() if inverted else cube
            for symmetry_index in _SEARCH_SYMMETRIES:
                transformed = (
                    self.symmetries[symmetry_index]
                    * source
                    * self.symmetries.inverse[symmetry_index]
                )
                if any(variant.cube == transformed for variant in variants):
                    continue
                variants.append(_SearchVariant(transformed, symmetry_index, inverted))
        return variants

    def restore_solution(
        self, solution: list[Move], variant: _SearchVariant
    ) -> list[Move]:
        """Map a variant's solution back to the original cube orientation."""
        inverse_symmetry = self.inverse_symmetry_indices[variant.symmetry_index]
        restored = [
            Move(self.tables.move_conj[MOVES * inverse_symmetry + move])
            for move in solution
        ]
        if variant.inverted:
            restored = [
                Move((move // 3) * 3 + (2 - move % 3)) for move in reversed(restored)
            ]
        return restored

    @staticmethod
    def phase1_from_cube(cube: CubieCube) -> Phase1State:
        return Phase1State(
            cube.twist,
            cube.flip,
            cube.ud_slice_sorted,
            cube.u_edges_sorted,
            cube.d_edges_sorted,
            cube.corner,
        )

    def apply_phase1_move(self, state: Phase1State, move: int) -> Phase1State:
        """Apply a move to every phase 1 coordinate."""
        tables = self.tables
        return Phase1State(
            tables.twist_move[MOVES * state.twist + move],
            tables.flip_move[MOVES * state.flip + move],
            tables.ud_slice_sorted_move[MOVES * state.ud_slice_sorted + move],
            tables.u_edges_sorted_move[MOVES * state.u_edges_sorted + move],
            tables.d_edges_sorted_move[MOVES * state.d_edges_sorted + move],
            tables.corner_move[MOVES * state.corner + move],
        )

    def phase1_distance_after_move(
        self, state: Phase1State, move: int, previous_distance: int
    ) -> int:
        """Compute the pruning distance without allocating a successor state."""
        tables = self.tables
        twist = tables.twist_move[MOVES * state.twist + move]
        flip = tables.flip_move[MOVES * state.flip + move]
        ud_slice_sorted = tables.ud_slice_sorted_move[
            MOVES * state.ud_slice_sorted + move
        ]

        # Inline the depth-mod-3 lookup here because this runs for every candidate
        # move. The general helper remains useful for the much less frequent pruning
        # gradient walk.
        flip_ud_slice = FLIP_MAX * (ud_slice_sorted // EDGE4_MAX) + flip
        symmetry_class = tables.flip_ud_slice_class_lookup[flip_ud_slice]
        symmetry = tables.flip_ud_slice_symmetry_lookup[flip_ud_slice]
        prune_index = (
            TWIST_MAX * symmetry_class
            + tables.twist_conj[SYMMETRIES_D4H * twist + symmetry]
        )
        depth_mod3 = tables.flip_ud_slice_class_twist_prune[prune_index]
        return tables.depth_lookup[3 * previous_distance + depth_mod3]

    def phase2_from_phase1(self, state: Phase1State) -> Phase2State:
        tables = self.tables
        edge8 = tables.edge_merge[
            EDGE4_MAX * state.u_edges_sorted + state.d_edges_sorted % EDGE4_MAX
        ]
        return Phase2State(state.ud_slice_sorted, edge8, state.corner)

    def apply_phase2_move(self, state: Phase2State, move: int) -> Phase2State:
        tables = self.tables
        corner = tables.corner_move[MOVES * state.corner + move]
        return Phase2State(
            tables.ud_slice_sorted_move[MOVES * state.edge4 + move],
            tables.edge8_move[MOVES * state.edge8 + move],
            corner,
        )

    def _phase1_depth_mod3(self, twist: int, flip: int, ud_slice_sorted: int) -> int:
        tables = self.tables
        flip_ud_slice = FLIP_MAX * (ud_slice_sorted // EDGE4_MAX) + flip
        symmetry_class = tables.flip_ud_slice_class_lookup[flip_ud_slice]
        symmetry = tables.flip_ud_slice_symmetry_lookup[flip_ud_slice]
        return tables.flip_ud_slice_class_twist_prune[
            TWIST_MAX * symmetry_class
            + tables.twist_conj[SYMMETRIES_D4H * twist + symmetry]
        ]

    def phase1_depth_mod3(self, state: Phase1State) -> int:
        return self._phase1_depth_mod3(state.twist, state.flip, state.ud_slice_sorted)

    def _phase2_depth_mod3(self, edge8: int, corner: int) -> int:
        tables = self.tables
        symmetry_class = tables.corner_class_lookup[corner]
        symmetry = tables.corner_symmetry_lookup[corner]
        return tables.corner_class_edge8_prune[
            EDGE8_MAX * symmetry_class
            + tables.edge8_conj[SYMMETRIES_D4H * edge8 + symmetry]
        ]

    def phase2_depth_mod3(self, state: Phase2State) -> int:
        return self._phase2_depth_mod3(state.edge8, state.corner)

    def phase1_distance(self, state: Phase1State) -> int:
        """Recover the exact G1 distance from a depth-mod-3 pruning table."""
        depth_mod3 = self.phase1_depth_mod3(state)
        depth = 0

        while not self.phase1_complete(state):
            if depth_mod3 == 0:
                depth_mod3 = 3
            for move in PHASE_1_MOVES:
                next_state = self.apply_phase1_move(state, move)
                if self.phase1_depth_mod3(next_state) == depth_mod3 - 1:
                    state = next_state
                    depth += 1
                    depth_mod3 -= 1
                    break
            else:
                raise RuntimeError("phase 1 pruning gradient is broken")
        return depth

    def phase2_distance(self, state: Phase2State) -> int:
        """Recover the exact corner × edge8 distance used as a lower bound."""
        depth_mod3 = self.phase2_depth_mod3(state)
        if depth_mod3 == 3:
            # The pruning table was intentionally not filled to this depth. This lower
            # bound exceeds the maximum phase 2 search depth.
            return PHASE_2_PRUNE_UNFILLED_DEPTH

        depth = 0
        # This table covers corner × edge8 only; edge4 is covered by the independent
        # cornslice heuristic used by the search. Keep these as scalar values because
        # this gradient walk is run for every phase 1 leaf.
        edge8, corner = state.edge8, state.corner
        tables = self.tables
        while edge8 != 0 or corner != 0:
            if depth_mod3 == 0:
                depth_mod3 = 3
            for move in PHASE_2_MOVES:
                next_corner = tables.corner_move[MOVES * corner + move]
                next_edge8 = tables.edge8_move[MOVES * edge8 + move]
                if self._phase2_depth_mod3(next_edge8, next_corner) == depth_mod3 - 1:
                    edge8, corner = next_edge8, next_corner
                    depth += 1
                    depth_mod3 -= 1
                    break
            else:
                raise RuntimeError("phase 2 pruning gradient is broken")
        return depth

    def phase2_distance_after_move(
        self, previous_distance: int, state: Phase2State
    ) -> int:
        """Derive a neighbour's distance, falling back for unfilled entries."""
        depth_mod3 = self.phase2_depth_mod3(state)
        if depth_mod3 == 3:
            # Be optimistic and let the independent cornslice table do the pruning.
            return 0
        return self.tables.depth_lookup[3 * previous_distance + depth_mod3]

    def cornslice_distance(self, state: Phase2State) -> int:
        return self.tables.cornslice_prune[EDGE4_MAX * state.corner + state.edge4]

    @staticmethod
    def phase1_complete(state: Phase1State) -> bool:
        return (
            state.twist == 0
            and state.flip == 0
            and state.ud_slice_sorted // EDGE4_MAX == 0
        )

    @staticmethod
    def phase2_complete(state: Phase2State) -> bool:
        return state.edge4 == 0 and state.edge8 == 0 and state.corner == 0


class _SearchSession:
    """
    Mutable control state for one search invocation.

    Cube states remain immutable and are passed down the recursion. Only the current
    move path, incumbent bound, timeout bookkeeping, and newly found solutions mutate.
    Keeping this state per invocation makes the reusable solver safe for concurrent
    calls.
    """

    def __init__(
        self,
        coordinates: _CoordinateModel,
        cube: CubieCube,
        max_length: int,
        deadline: float,
        cancelled: Event,
        *,
        stop_on_first: bool,
    ) -> None:
        self.coordinates = coordinates
        self.root = coordinates.phase1_from_cube(cube)
        self.max_length = max_length
        self.deadline = deadline
        self.cancelled = cancelled
        self.stop_on_first = stop_on_first

        self.path: list[int] = []
        self.shortest_length = max_length + 1
        self.node_count = 0
        self.locally_stopped = False
        self.new_solutions: list[list[Move]] = []

    def run(self) -> Generator[list[Move]]:
        if self.max_length < 0 or self._deadline_reached():
            return

        phase1_min_distance = self.coordinates.phase1_distance(self.root)

        # max_length is inclusive: phase 1 may consume the entire move budget when
        # phase 2 needs zero moves.
        for phase1_budget in range(phase1_min_distance, self.max_length + 1):
            if phase1_budget >= self.shortest_length:
                break

            self.new_solutions.clear()
            self._search_phase1(self.root, phase1_min_distance, phase1_budget)
            yield from self.new_solutions

            if self._should_stop():
                break

    def _search_phase1(self, state: Phase1State, distance: int, remaining: int) -> None:
        if not self._visit_node():
            return

        if remaining == 0:
            self._start_phase2(state)
            return

        if distance > remaining:
            return

        # If phase 1 is already complete, let phase 2 search its own moves unless the
        # phase 1 budget is large enough that deferring them could harm completeness.
        defer_phase2_moves = distance == 0 and remaining < 5

        if self.path:
            successors = (
                _PHASE_1_DEFERRED_SUCCESSORS[self.path[-1]]
                if defer_phase2_moves
                else _PHASE_1_SUCCESSORS[self.path[-1]]
            )
        else:
            successors = (
                _PHASE_1_DEFERRED_MOVES if defer_phase2_moves else _PHASE_1_ROOT_MOVES
            )

        for move in successors:
            next_distance = self.coordinates.phase1_distance_after_move(
                state, move, distance
            )
            if next_distance >= remaining:
                continue

            next_state = self.coordinates.apply_phase1_move(state, move)
            self.path.append(move)
            self._search_phase1(next_state, next_distance, remaining - 1)
            self.path.pop()

            if self._should_stop():
                return

    def _start_phase2(self, phase1_state: Phase1State) -> None:
        if self._deadline_reached():
            return

        state = self.coordinates.phase2_from_phase1(phase1_state)
        budget_limit = min(self.shortest_length - len(self.path), MAX_PHASE2_DEPTH)

        # Two independent heuristics cheaply reject unpromising G1 states.
        if self.coordinates.cornslice_distance(state) >= budget_limit:
            return
        min_distance = self.coordinates.phase2_distance(state)
        if min_distance >= budget_limit:
            return

        for budget in range(min_distance, budget_limit):
            if self._search_phase2(state, min_distance, budget):
                return
            if self._should_stop():
                return

    def _search_phase2(self, state: Phase2State, distance: int, remaining: int) -> bool:
        if not self._visit_node():
            return False

        if self.coordinates.phase2_complete(state):
            self._record_solution()
            return True

        if distance > remaining:
            return False

        successors = (
            _PHASE_2_SUCCESSORS[self.path[-1]] if self.path else _PHASE_2_ROOT_MOVES
        )
        for move in successors:
            next_state = self.coordinates.apply_phase2_move(state, move)
            next_distance = self.coordinates.phase2_distance_after_move(
                distance, next_state
            )
            cornslice_distance = self.coordinates.cornslice_distance(next_state)
            if max(next_distance, cornslice_distance) >= remaining:
                continue

            self.path.append(move)
            solved = self._search_phase2(next_state, next_distance, remaining - 1)
            self.path.pop()

            if solved or self._should_stop():
                return solved

        return False

    def _record_solution(self) -> None:
        length = len(self.path)
        if length >= self.shortest_length:
            return

        self.shortest_length = length
        self.new_solutions.append([Move(move) for move in self.path])
        if self.stop_on_first:
            self.locally_stopped = True
            self.cancelled.set()

    def _should_stop(self) -> bool:
        return self.locally_stopped or self.cancelled.is_set()

    def _visit_node(self) -> bool:
        if self._should_stop():
            return False

        self.node_count += 1
        if self.node_count % _TIMEOUT_CHECK_INTERVAL == 0:
            return not self._deadline_reached()
        return True

    def _deadline_reached(self) -> bool:
        if time.monotonic() <= self.deadline:
            return False
        self.locally_stopped = True
        self.cancelled.set()
        return True


class _SearchPortfolio:
    """
    Coordinate independent searches of symmetry-equivalent cube states.

    Workers share a deadline and cancellation signal but no mutable DFS state. This
    makes each search tree independent while allowing the first successful ordering to
    stop the rest.
    """

    def __init__(
        self,
        coordinates: _CoordinateModel,
        cube: CubieCube,
        max_length: int,
        timeout: float,
    ) -> None:
        self.coordinates = coordinates
        self.variants = coordinates.search_variants(cube)
        self.max_length = max_length
        self.deadline = time.monotonic() + timeout
        self.cancelled = Event()

    def _session(
        self, variant: _SearchVariant, *, stop_on_first: bool
    ) -> _SearchSession:
        return _SearchSession(
            self.coordinates,
            variant.cube,
            self.max_length,
            self.deadline,
            self.cancelled,
            stop_on_first=stop_on_first,
        )

    def _first_solution_for(self, variant: _SearchVariant) -> list[Move] | None:
        solution = next(self._session(variant, stop_on_first=True).run(), None)
        if solution is None:
            return None
        return self.coordinates.restore_solution(solution, variant)

    def first_solution(self) -> list[Move] | None:
        with ThreadPoolExecutor(max_workers=len(self.variants)) as executor:
            futures = [
                executor.submit(self._first_solution_for, variant)
                for variant in self.variants
            ]
            try:
                for future in as_completed(futures):
                    solution = future.result()
                    if solution is not None:
                        return solution
            finally:
                self.cancelled.set()
        return None

    def _collect_solutions(
        self, variant: _SearchVariant, results: Queue[list[Move] | _WorkerDone]
    ) -> None:
        try:
            for solution in self._session(variant, stop_on_first=False).run():
                results.put(self.coordinates.restore_solution(solution, variant))
        except BaseException as error:
            results.put(_WorkerDone(error))
        else:
            results.put(_WorkerDone())

    def progressive_solutions(self) -> Generator[list[Move]]:
        results: Queue[list[Move] | _WorkerDone] = Queue()
        executor = ThreadPoolExecutor(max_workers=len(self.variants))
        futures = [
            executor.submit(self._collect_solutions, variant, results)
            for variant in self.variants
        ]
        completed = 0
        shortest_length = self.max_length + 1

        try:
            while completed < len(self.variants):
                result = results.get()
                if isinstance(result, _WorkerDone):
                    completed += 1
                    if result.error is not None:
                        raise result.error
                elif len(result) < shortest_length:
                    shortest_length = len(result)
                    yield result
        finally:
            self.cancelled.set()
            executor.shutdown(wait=True, cancel_futures=True)
            # Surface an unexpected executor failure that happened before the worker
            # could put its completion marker on the queue.
            for future in futures:
                if future.done() and not future.cancelled():
                    future.result()
