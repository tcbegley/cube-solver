import array

from tqdm import tqdm

from twophase.constants import (
    CORNER_CLASSES,
    CORNER_MAX,
    FLIP_MAX,
    FLIP_UD_SLICE_CLASSES,
    SYMMETRIES_D4H,
    UD_SLICE_MAX,
)
from twophase.tables._array import dtype_to_max_val, dtypes, max_val_to_dtype
from twophase.tables.cubiecube import CubieCube
from twophase.tables.symmetries import Symmetries


def _make_symmetry_tables(
    name: str, max_val: int, num_classes: int, edge: bool
) -> tuple[array.array, array.array, array.array]:
    class_dtype = max_val_to_dtype(num_classes)
    coord_dtype = max_val_to_dtype(max_val)

    class_max = dtype_to_max_val(class_dtype)

    class_lookup = array.array(class_dtype, [class_max] * max_val)
    symmetry_lookup = array.array(dtypes.u8, [dtype_to_max_val(dtypes.u8)] * max_val)
    representative_lookup = array.array(
        coord_dtype, [dtype_to_max_val(coord_dtype)] * num_classes
    )

    symmetries = Symmetries(subgroup=True)

    class_index = 0
    cube = CubieCube()

    pbar = tqdm(total=SYMMETRIES_D4H * max_val, desc=f"{name} symmetry tables")

    for coord in range(max_val):
        if class_lookup[coord] == class_max:
            # this is the first time we've encountered the value coord, we'll make this
            # cube the representative, and add all equivalent cubes to the class by
            # conjugating with all of the possible symmetries
            class_lookup[coord] = class_index
            symmetry_lookup[coord] = 0
            representative_lookup[class_index] = coord

            setattr(cube, name, coord)

            for symmetry_index, symmetry in enumerate(symmetries):
                if edge:
                    conj_cube = symmetries.inverse[symmetry_index].edge_multiply(
                        cube.edge_multiply(symmetry)
                    )
                else:
                    conj_cube = symmetries.inverse[symmetry_index].corner_multiply(
                        cube.corner_multiply(symmetry)
                    )
                coord_new = getattr(conj_cube, name)
                if class_lookup[coord_new] == class_max:
                    class_lookup[coord_new] = class_index
                    symmetry_lookup[coord_new] = symmetry_index
            class_index += 1

        pbar.update(SYMMETRIES_D4H)

    return class_lookup, symmetry_lookup, representative_lookup


def make_flip_ud_slice_symmetry_tables() -> tuple[
    array.array, array.array, array.array
]:
    return _make_symmetry_tables(
        "flip_ud_slice", FLIP_MAX * UD_SLICE_MAX, FLIP_UD_SLICE_CLASSES, edge=True
    )


def make_corner_symmetry_tables() -> tuple[array.array, array.array, array.array]:
    return _make_symmetry_tables("corner", CORNER_MAX, CORNER_CLASSES, edge=False)
