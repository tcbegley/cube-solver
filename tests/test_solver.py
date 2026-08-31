import random
from concurrent.futures import ThreadPoolExecutor

import pytest

from twophase.pieces import Move
from twophase.solve.solver import Solver
from twophase.tables.cubiecube import CubieCube, Moves


@pytest.fixture(scope="module")
def solver():
    return Solver()


CUBE_MOVES = Moves()


def _apply_moves(cube: CubieCube, moves: list[Move]) -> CubieCube:
    """Apply a sequence of moves to a cube and return the result."""
    for m in moves:
        mv = CUBE_MOVES[m]
        assert isinstance(mv, CubieCube)
        cube = cube.multiply(mv)
    return cube


def _is_solved(cube: CubieCube) -> bool:
    return cube == CubieCube()


class TestSolvedCube:
    def test_returns_empty_list(self, solver):
        solution = solver.solve(CubieCube())
        assert solution == []


class TestSimpleCubes:
    @pytest.mark.parametrize(
        "scramble",
        [[Move.U1], [Move.R2], [Move.F3], [Move.R2, Move.U1, Move.L1]],
        ids=["U", "R2", "F'", "R2 U L"],
    )
    def test_finds_solution(self, solver, scramble):
        cube = _apply_moves(CubieCube(), scramble)
        solution = solver.solve(cube, timeout=5)

        assert solution is not None
        assert _is_solved(_apply_moves(cube, solution))

    def test_r2_u_l_optimal(self, solver):
        """R2 U L should be solvable in 3 moves: L' U' R2."""
        cube = _apply_moves(CubieCube(), [Move.R2, Move.U1, Move.L1])
        *_, solution = solver.solve_progressively(cube, timeout=5)

        assert len(solution) == 3


class TestComplexCubes:
    @pytest.mark.parametrize("seed", range(5))
    def test_random_scramble_is_solvable(self, solver, seed):
        rng = random.Random(seed)
        scramble = [Move(rng.randint(0, 17)) for _ in range(25)]
        cube = _apply_moves(CubieCube(), scramble)
        solution = solver.solve(cube, timeout=10)

        assert solution is not None
        assert _is_solved(_apply_moves(cube, solution))
        assert len(solution) <= 20


class TestMaxLength:
    def test_solved_cube_with_zero_length_bound(self, solver):
        assert solver.solve(CubieCube(), max_length=0) == []

    def test_exact_bound_may_be_spent_entirely_in_phase_1(self, solver):
        cube = _apply_moves(CubieCube(), [Move.F1])
        solution = solver.solve(cube, max_length=1, timeout=5)

        assert solution == [Move.F3]

    def test_respects_max_length(self, solver):
        cube = _apply_moves(CubieCube(), [Move.R2, Move.U1, Move.L1])
        solution = solver.solve(cube, max_length=3, timeout=5)

        assert solution is not None
        assert len(solution) <= 3

    def test_returns_none_when_max_length_too_short(self, solver):
        cube = _apply_moves(CubieCube(), [Move.R2, Move.U1, Move.L1])
        # max_length=1 is too short for a 3-move solution
        solution = solver.solve(cube, max_length=1, timeout=5)

        assert solution is None


class TestSearchVariants:
    def test_each_variant_maps_its_solution_back_to_the_original_cube(self, solver):
        cube = _apply_moves(CubieCube(), [Move.R2, Move.U1, Move.L1])
        variants = solver._coordinates.search_variants(cube)

        assert len(variants) == 6
        for variant in variants:
            solution = solver.solve(variant.cube, max_length=3, timeout=5)
            assert solution is not None

            restored = solver._coordinates.restore_solution(solution, variant)
            assert _is_solved(_apply_moves(cube, restored))


class TestConcurrentUse:
    def test_search_state_is_not_shared_between_calls(self, solver):
        cubes = []
        for seed in range(3):
            rng = random.Random(seed)
            scramble = [Move(rng.randint(0, 17)) for _ in range(25)]
            cubes.append(_apply_moves(CubieCube(), scramble))

        with ThreadPoolExecutor(max_workers=len(cubes)) as executor:
            solutions = list(executor.map(solver.solve, cubes))

        for cube, solution in zip(cubes, solutions):
            assert solution is not None
            assert _is_solved(_apply_moves(cube, solution))


class TestTimeout:
    def test_returns_none_when_no_solution_found_in_time(self, solver):
        rng = random.Random(42)
        scramble = [Move(rng.randint(0, 17)) for _ in range(25)]
        cube = _apply_moves(CubieCube(), scramble)
        # very short timeout — may not find anything
        solution = solver.solve(cube, timeout=0.0001)

        # either None or a valid solution
        if solution is not None:
            assert _is_solved(_apply_moves(cube, solution))
