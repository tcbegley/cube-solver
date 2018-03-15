# cube-solver
A pure python implementation of Herbert Kociemba's two-phase algorithm for solving the Rubik's Cube

Better interface and documentation to come, for now, try it as follows

```
from solve import Solver

s = Solver()
s.solve("<cube_string>")
```
Where the cube string is a 54 character string, consisting of the characters U, R, F, D, L, B (corresponding to the Upper, Right, Front, Down, Left and Back faces). Each character corresponds to one of the 54 stickers on the cube:

```
            |------------|
            |-U1--U2--U3-|
            |------------|
            |-U4--U5--U6-|
            |------------|
            |-U7--U8--U9-|
            |------------|
------------|------------|------------|------------
-L1--L2--L3-|-F1--F2--F3-|-R1--R2--R3-|-B1--B2--B3-
------------|------------|------------|------------
-L4--L5--L6-|-F4--F5--F6-|-R4--R5--R6-|-B4--B5--B6-
------------|------------|------------|------------
-L7--L8--L9-|-F7--F8--F9-|-R7--R8--R9-|-B7--B8--B9-
------------|------------|------------|------------
            |------------|
            |-D1--D2--D3-|
            |------------|
            |-D4--D5--D6-|
            |------------|
            |-D7--D8--D9-|
            |------------|
```

and should be specified in the order U1-U9, R1-R9, F1-F9, D1-D9, L1-L9, B1-B9.

For example, a completely solved cube is represented by the string `"UUUUUUUUURRRRRRRRRFFFFFFFFDDDDDDDDDLLLLLLLLLBBBBBBBB"`.

Solve will search until the shortest solution has been found or timeout has been reached (default is 10 seconds). Typically it will find a solution instantly, and improve on it once or twice. I believe in principle it should eventually find an optimal solution, but usually times out before it can.
