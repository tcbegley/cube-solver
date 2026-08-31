# twophase

An educational Python implementation of Herbert Kociemba's two-phase algorithm
for solving a Rubik's Cube.

The project models a cube as its movable corner and edge pieces, represents
states with compact coordinates, and uses generated move and pruning tables to
search for solutions. The implementation favors readable, well-tested Python
alongside the optimizations needed for a practical solver.

## Usage

Pass a 54-character facelet string in `U R F D L B` face order to `solve`:

```python
from twophase import solve

cube = "UUUUUUUUURRRRRRRRRFFFFFFFFFDDDDDDDDDLLLLLLLLLBBBBBBBBB"
assert solve(cube) == ""
```

`solve` returns a space-separated sequence in standard cube notation, or
`None` when a solution cannot be found before the requested length or time
limit. For lower-level use, `parse` converts a facelet string to a `CubieCube`,
`Solver` returns `Move` values, and `format_moves` renders those values.

```python
from twophase import Solver, format_moves, parse

moves = Solver().solve(parse(cube))
print(format_moves(moves or []))
```

The first solve generates lookup tables. Pass `cache_path` to `Solver` or the
high-level helpers to choose where they are stored.

## Development

This repository uses [uv](https://docs.astral.sh/uv/) to manage its Python
environment and lock file:

```sh
uv sync --all-groups
uv run pytest
```
