# twophase

A pure-Python implementation of Herbert Kociemba's two-phase algorithm for
solving a Rubik's Cube.

## Installation

Requires Python 3.12 or later. Add it to your `uv` project directly from GitHub:

```sh
uv add git+https://github.com/tcbegley/cube-solver.git
```

Without uv, install it with pip instead:

```sh
pip install git+https://github.com/tcbegley/cube-solver.git
```

## Usage

Pass `solve` a 54-character string that describes the cube's stickers:

```python
from twophase import solve

cube = "UUUUUUUUUBBBRRRRRRRRRFFFFFFDDDDDDDDDFFFLLLLLLLLLBBBBBB"
print(solve(cube))  # U'
```

> [!IMPORTANT]
> The first solve generates the coordinate and pruning tables used by the
> search. This can take several minutes. The tables are cached for later runs;
> pass `cache_path` to `solve` or `solve_progressively` to store them elsewhere.

The result is a space-separated sequence in standard cube notation (`U`, `R2`,
`F'`, and so on). `solve` returns `None` when it cannot find a solution within
its limits; use `max_length` and `timeout` to adjust the default 20-move and
10-second limits.

```python
solution = solve(cube, max_length=22, timeout=30)
```

### Cube strings

A cube string contains the sticker colours `U`, `R`, `F`, `D`, `L`, and `B` in
this order: U1–U9, R1–R9, F1–F9, D1–D9, L1–L9, B1–B9.

```text
             |------------|
             |-U1--U2--U3-|
             |------------|
             |-U4--U5--U6-|
             |------------|
             |-U7--U8--U9-|
|------------|------------|------------|------------|
|-L1--L2--L3-|-F1--F2--F3-|-R1--R2--R3-|-B1--B2--B3-|
|------------|------------|------------|------------|
|-L4--L5--L6-|-F4--F5--F6-|-R4--R5--R6-|-B4--B5--B6-|
|------------|------------|------------|------------|
|-L7--L8--L9-|-F7--F8--F9-|-R7--R8--R9-|-B7--B8--B9-|
|------------|------------|------------|------------|
             |-D1--D2--D3-|
             |------------|
             |-D4--D5--D6-|
             |------------|
             |-D7--D8--D9-|
             |------------|
```

For example, a solved cube is:

```text
UUUUUUUUURRRRRRRRRFFFFFFFFFDDDDDDDDDLLLLLLLLLBBBBBBBBB
```

### Finding shorter solutions

`solve_progressively` yields increasingly shorter solutions until it reaches
the time limit:

```python
from twophase import solve_progressively

for solution in solve_progressively(cube, timeout=30):
    print(solution)
```

### Lower-level interface

For applications that need the cube model or moves rather than a formatted
string, use `parse`, `Solver`, and `format_moves`:

```python
from twophase import Solver, format_moves, parse

moves = Solver().solve(parse(cube))
if moves is not None:
    print(format_moves(moves))
```
