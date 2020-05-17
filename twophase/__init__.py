import time

from .solve import SolutionManager


def solve(cube_string, max_length=25, max_time=10):
    sm = SolutionManager(cube_string)
    solution = sm.solve(max_length, time.time() + max_time)
    if isinstance(solution, str):
        return solution
    elif solution == -2:
        raise RuntimeError("max_time exceeded, no solution found")
    elif solution == -1:
        raise RuntimeError("no solution found, try increasing max_length")
    raise RuntimeError(
        f"unexpected return value from SolutionManager.solve: {solution}"
    )
