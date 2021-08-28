# cube-solver

A pure Python implementation of Herbert Kociemba's two-phase algorithm for solving the Rubik's Cube

## Installation

Requires Python 3. Install with

```sh
pip install git+https://github.com/tcbegley/cube-solver.git
```

Note that depending on how your system is configured, you may need to replace `pip` with `pip3` in the above command to install for Python 3.

## Usage

To solve a cube, just import the `solve` method and pass a cube string.

```python
from twophase import solve

solve("<cube_string>")
```

Where the cube string is a 54 character string, consisting of the characters U, R, F, D, L, B (corresponding to the Upper, Right, Front, Down, Left and Back faces). Each character corresponds to one of the 54 stickers on the cube:

```plaintext
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

and should be specified in the order U1-U9, R1-R9, F1-F9, D1-D9, L1-L9, B1-B9.

For example, a completely solved cube is represented by the string `"UUUUUUUUURRRRRRRRRFFFFFFFFFDDDDDDDDDLLLLLLLLLBBBBBBBBB"`.

`solve` will return a solution unless timeout has been reached (default is 10 seconds). Typically it will find a solution very quickly unless you set a low upper bound on the number of moves allowed. Note that the first time you run `solve`, it will precompute move tables needed for the solution which might take ~1 minute. Subsequent runs will be much faster.

If you want to keep searching for better solutions, use the `solve_best` or
`solve_best_generator` functions. `solve_best` reduces `max_length` each time a
solution is found and continues searching for a better solution. All solutions
found are returned in a list at the end. `solve_best_generator` creates a
generator that yields solutions as they are found.

```python
from twophase import solve_best, solve_best_generator

# returns a list of solutions
solve_best("<cube_string>")

# creates a generator that yields solutions as they are found
solve_best_generator("<cube_string>")
```
