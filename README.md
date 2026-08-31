# twophase

An educational Python implementation of Herbert Kociemba's two-phase algorithm
for solving a Rubik's Cube.

The project models a cube as its movable corner and edge pieces, represents
states with compact coordinates, and uses generated move and pruning tables to
search for solutions. The implementation favors readable, well-tested Python
alongside the optimizations needed for a practical solver.

## Development

This repository uses [uv](https://docs.astral.sh/uv/) to manage its Python
environment and lock file:

```sh
uv sync --all-groups
uv run pytest
```

The public parsing and solving interface is introduced with the solver.
