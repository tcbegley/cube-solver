import pytest

from twophase.constants import EDGE4_MAX, EDGE8_MAX, MOVES, SYMMETRIES_D4H, TWIST_MAX
from twophase.tables.cubiecube import CubieCube, move
from twophase.tables.symmetries import Symmetries


def test_table_attributes(tables):
    for coord in [
        "twist",
        "flip",
        "ud_slice_sorted",
        "u_edges_sorted",
        "d_edges_sorted",
        "edge8",
        "corner",
    ]:
        assert hasattr(tables, f"{coord}_move")
    assert hasattr(tables, "move_conj")
    for coord in ["twist", "edge8"]:
        assert hasattr(tables, f"{coord}_conj")
    for coord in ["corner", "flip_ud_slice"]:
        assert hasattr(tables, f"{coord}_class_lookup")
        assert hasattr(tables, f"{coord}_symmetry_lookup")
        assert hasattr(tables, f"{coord}_representative_lookup")


def _test_move_table_consistency(tables, name, value, mv, phase_2_only=False):
    cube = CubieCube()
    setattr(cube, name, value)

    for rot in range(3):
        cube = move(cube, mv)
        if phase_2_only and mv % 3 != 0 and rot % 2 == 0:
            assert getattr(tables, f"{name}_move")[MOVES * value + 3 * mv + rot] == 0
        else:
            assert getattr(tables, f"{name}_move")[
                MOVES * value + 3 * mv + rot
            ] == getattr(cube, name)


@pytest.mark.parametrize("twist", [0, 123, 1_000, 2_186])
@pytest.mark.parametrize("mv", range(6))
def test_twist_move_table(tables, twist, mv):
    _test_move_table_consistency(tables, "twist", twist, mv)


@pytest.mark.parametrize("flip", [0, 123, 1_000, 2_047])
@pytest.mark.parametrize("mv", range(6))
def test_flip_move_table(tables, flip, mv):
    _test_move_table_consistency(tables, "flip", flip, mv)


@pytest.mark.parametrize("ud_slice_sorted", [0, 123, 1_000, 10_000, 11_879])
@pytest.mark.parametrize("mv", range(6))
def test_ud_slice_sorted_move_table(tables, ud_slice_sorted, mv):
    _test_move_table_consistency(tables, "ud_slice_sorted", ud_slice_sorted, mv)


@pytest.mark.parametrize("u_edges_sorted", [0, 123, 1_000, 10_000, 11_879])
@pytest.mark.parametrize("mv", range(6))
def test_u_edges_sorted_move_table(tables, u_edges_sorted, mv):
    _test_move_table_consistency(tables, "u_edges_sorted", u_edges_sorted, mv)


@pytest.mark.parametrize("d_edges_sorted", [0, 123, 1_000, 10_000, 11_879])
@pytest.mark.parametrize("mv", range(6))
def test_d_edges_sorted_move_table(tables, d_edges_sorted, mv):
    _test_move_table_consistency(tables, "d_edges_sorted", d_edges_sorted, mv)


@pytest.mark.parametrize("edge8", [0, 123, 1_000, 10_000, 40_319])
@pytest.mark.parametrize("mv", range(6))
def test_edge8_move_table(tables, edge8, mv):
    _test_move_table_consistency(tables, "edge8", edge8, mv, phase_2_only=True)


@pytest.mark.parametrize("corner", [0, 123, 1_000, 10_000, 40_319])
@pytest.mark.parametrize("mv", range(6))
def test_corner_move_table(tables, corner, mv):
    _test_move_table_consistency(tables, "corner", corner, mv)


@pytest.mark.parametrize(
    "sym,move,conj",
    [
        (0, 0, 0),
        (0, 1, 1),
        (10, 0, 9),
        (10, 1, 10),
        (11, 12, 17),
        (42, 15, 6),
        (47, 17, 15),
    ],
)
def test_move_conj_table(tables, sym, move, conj):
    assert tables.move_conj[MOVES * sym + move] == conj


def _test_conj_table_consistency(tables, name, value):
    cube = CubieCube()
    setattr(cube, name, value)
    symmetries = Symmetries(subgroup=True)

    for s, sym in enumerate(symmetries):
        conj_cube = sym * cube * symmetries.inverse[s]
        assert getattr(tables, f"{name}_conj")[SYMMETRIES_D4H * value + s] == getattr(
            conj_cube, name
        )


@pytest.mark.parametrize("twist", [0, 123, 1_000, 2_186])
def test_twist_conj_table(tables, twist):
    _test_conj_table_consistency(tables, "twist", twist)


@pytest.mark.parametrize("edge8", [0, 123, 1_000, 10_000, 40_319])
def test_edge8_conj_table(tables, edge8):
    _test_conj_table_consistency(tables, "edge8", edge8)


def _test_symmetry_tables(tables, name, coord, class_index, symmetry, representative):
    assert getattr(tables, f"{name}_class_lookup")[coord] == class_index
    assert getattr(tables, f"{name}_symmetry_lookup")[coord] == symmetry
    assert (
        getattr(tables, f"{name}_representative_lookup")[class_index] == representative
    )


@pytest.mark.parametrize(
    "corner,class_index,symmetry,representative",
    [
        (0, 0, 0, 0),
        (1_234, 165, 2, 239),
        (10_000, 220, 9, 350),
        (40_000, 189, 9, 319),
        (40_319, 2_753, 2, 28_783),
    ],
)
def test_corner_symmetry_tables(tables, corner, class_index, symmetry, representative):
    _test_symmetry_tables(
        tables, "corner", corner, class_index, symmetry, representative
    )


@pytest.mark.parametrize(
    "flip_ud_slice,class_index,symmetry,representative",
    [
        (0, 0, 0, 0),
        (1_234, 103, 2, 429),
        (10_000, 4_090, 1, 8_000),
        (100_000, 11_380, 7, 40_382),
        (1_000_000, 16_296, 11, 66_094),
        (1_013_759, 18_061, 10, 143_232),
    ],
)
def test_flip_ud_slice_symmetry_tables(
    tables, flip_ud_slice, class_index, symmetry, representative
):
    _test_symmetry_tables(
        tables, "flip_ud_slice", flip_ud_slice, class_index, symmetry, representative
    )


def _test_symmetry_tables_consistency(tables, name, coord):
    symmetries = Symmetries(subgroup=True)

    # initialise cube with given coordinate
    cube = CubieCube()
    setattr(cube, name, coord)
    # find the representative of the original cube's equivalence class
    rep = CubieCube()
    setattr(
        rep,
        name,
        getattr(tables, f"{name}_representative_lookup")[
            getattr(tables, f"{name}_class_lookup")[coord]
        ],
    )

    # the class of the cube and its representative should match
    assert (
        getattr(tables, f"{name}_class_lookup")[coord]
        == getattr(tables, f"{name}_class_lookup")[getattr(rep, name)]
    )

    # conjugating cube by the symmetry should recover the representative
    sym_index = getattr(tables, f"{name}_symmetry_lookup")[coord]
    conj_cube = symmetries[sym_index] * cube * symmetries.inverse[sym_index]
    assert getattr(conj_cube, name) == getattr(rep, name)


@pytest.mark.parametrize("corner", [0, 123, 1_234, 12_345, 34_567, 40_000, 40_319])
def test_corner_symmetry_tables_consistency(tables, corner):
    _test_symmetry_tables_consistency(tables, "corner", corner)


@pytest.mark.parametrize(
    "flip_ud_slice", [0, 123, 1_234, 12_345, 123_456, 1_000_000, 1_013_759]
)
def test_flip_ud_slice_symmetry_tables_consistency(tables, flip_ud_slice):
    _test_symmetry_tables_consistency(tables, "flip_ud_slice", flip_ud_slice)


def _test_pruning_table(tables, name, coord1, coord2, max_val2, pruning_value):
    assert getattr(tables, f"{name}_prune")[max_val2 * coord1 + coord2] == pruning_value


@pytest.mark.parametrize(
    "flip_ud_slice_class,twist,pruning_value",
    [
        (0, 0, 0),
        (1, 0, 1),
        (10, 20, 0),
        (1_234, 1_234, 2),
        (60_000, 2_000, 0),
        (64_429, 2_186, 2),
    ],
)
def test_flip_ud_slice_class_twist_pruning_table(
    tables, flip_ud_slice_class, twist, pruning_value
):
    _test_pruning_table(
        tables,
        "flip_ud_slice_class_twist",
        flip_ud_slice_class,
        twist,
        TWIST_MAX,
        pruning_value,
    )


@pytest.mark.parametrize(
    "corner_class,edge8,pruning_value",
    [
        (0, 0, 0),
        (39, 23_624, 1),
        (949, 25_039, 1),
        (1_145, 35_854, 1),
        (1_526, 28_658, 1),
        (1_549, 6_398, 0),
        (2_423, 9_480, 1),
    ],
)
def test_corner_class_edge8_pruning_table(tables, corner_class, edge8, pruning_value):
    _test_pruning_table(
        tables, "corner_class_edge8", corner_class, edge8, EDGE8_MAX, pruning_value
    )


@pytest.mark.parametrize(
    "edge_merge,edge8",
    [
        (0, 0),
        (123, 845),
        (1_234, 6_517),
        (12_345, 8_145),
        (40_000, 30_112),
        (40_319, 40_319),
    ],
)
def test_edge_merge_table(tables, edge_merge, edge8):
    assert tables.edge_merge[edge_merge] == edge8


@pytest.mark.parametrize("edge8", [0, 123, 1_234, 12_345, 40_000, 40_319])
def test_edge_merge_table_consistency(tables, edge8):
    cube = CubieCube()
    cube.edge8 = edge8

    assert (
        tables.edge_merge[
            EDGE4_MAX * cube.u_edges_sorted + cube.d_edges_sorted % EDGE4_MAX
        ]
        == edge8
    )


@pytest.mark.parametrize("depth", range(20))
def test_depth_lookup_table(tables, depth):
    for offset in range(-1, 2):
        new_depth = depth + offset
        if new_depth >= 0:
            assert tables.depth_lookup[3 * depth + new_depth % 3] == new_depth
