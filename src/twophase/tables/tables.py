from __future__ import annotations

import array
from pathlib import Path
from typing import Any, Callable

from twophase import constants
from twophase.tables import generators
from twophase.tables._array import BitpackedArray, dtypes, max_val_to_dtype
from twophase.tables._cache import resolve_cache_path

# hold tables associated with particular paths in memory. this is preferable to
# functools.cache because we can invalidate single entries without invalidating the
# entire cache
_TABLE_CACHE: dict[Path, Tables] = {}


def make_or_load_tables(cache_path: str | Path | None = None) -> Tables:
    """
    Load all move tables saved in the location specified by cache_path. If tables have
    already been loaded they will be retrieved from an in-memory cache.

    Parameters
    ----------
    cache_path : pathlike, optional
        The directory in which the move tables are stored.
    """
    cache_path = resolve_cache_path(cache_path)
    if cache_path not in _TABLE_CACHE:
        _TABLE_CACHE[cache_path] = Tables(cache_path)
    return _TABLE_CACHE[cache_path]


def delete_tables(cache_path: str | Path | None = None) -> None:
    """
    Delete all of the move tables stored in the directory specified by cache_path.

    Parameters
    ----------
    cache_path : pathlike, optional
        The directory in which the move tables to be deleted are stored.
    """
    cache_path = resolve_cache_path(cache_path)
    if cache_path in _TABLE_CACHE:
        del _TABLE_CACHE[cache_path]
    for table_path in cache_path.glob("*.bin"):
        table_path.unlink()


class Tables:
    # table attributes are created dynamically, so we need to add type hints manually
    # to keep mypy happy
    twist_move: array.array
    flip_move: array.array
    ud_slice_sorted_move: array.array
    u_edges_sorted_move: array.array
    d_edges_sorted_move: array.array
    edge8_move: array.array
    corner_move: array.array

    move_conj: array.array
    twist_conj: array.array
    edge8_conj: array.array

    corner_class_lookup: array.array
    corner_symmetry_lookup: array.array
    corner_representative_lookup: array.array
    flip_ud_slice_class_lookup: array.array
    flip_ud_slice_symmetry_lookup: array.array
    flip_ud_slice_representative_lookup: array.array

    flip_ud_slice_class_twist_prune: BitpackedArray
    corner_class_edge8_prune: BitpackedArray
    cornslice_prune: array.array

    edge_merge: array.array
    depth_lookup: array.array

    _move_tables: tuple[tuple[str, int, Callable[[], array.array]], ...] = (
        ("twist", constants.TWIST_MAX, generators.make_twist_move_table),
        ("flip", constants.FLIP_MAX, generators.make_flip_move_table),
        (
            "ud_slice_sorted",
            constants.UD_SLICE_MAX * constants.EDGE4_MAX,
            generators.make_ud_slice_sorted_move_table,
        ),
        (
            "u_edges_sorted",
            constants.UD_SLICE_MAX * constants.EDGE4_MAX,
            generators.make_u_edges_sorted_move_table,
        ),
        (
            "d_edges_sorted",
            constants.UD_SLICE_MAX * constants.EDGE4_MAX,
            generators.make_d_edges_sorted_move_table,
        ),
        ("edge8", constants.EDGE8_MAX, generators.make_edge8_move_table),
        ("corner", constants.CORNER_MAX, generators.make_corner_move_table),
    )
    _conj_tables: tuple[tuple[str, int, Callable[[], array.array]], ...] = (
        ("twist", constants.TWIST_MAX, generators.make_twist_conj_table),
        ("edge8", constants.EDGE8_MAX, generators.make_edge8_conj_table),
    )
    _sym_tables: tuple[
        tuple[
            str, int, int, Callable[[], tuple[array.array, array.array, array.array]]
        ],
        ...,
    ] = (
        (
            "corner",
            constants.CORNER_CLASSES,
            constants.CORNER_MAX,
            generators.make_corner_symmetry_tables,
        ),
        (
            "flip_ud_slice",
            constants.FLIP_UD_SLICE_CLASSES,
            constants.FLIP_MAX * constants.UD_SLICE_MAX,
            generators.make_flip_ud_slice_symmetry_tables,
        ),
    )

    def __init__(self, cache_path: Path) -> None:
        self.cache_path = cache_path
        self.load_tables()

    def _make_or_load_table(
        self, table_name: str, dtype: dtypes, constructor: Callable[[], array.array]
    ) -> None:
        table_path = self.cache_path / f"{table_name}.bin"
        if table_path.exists():
            table = array.array(dtype)
            table.frombytes(table_path.read_bytes())
        else:
            table = constructor()
            table_path.write_bytes(table.tobytes())
        setattr(self, table_name, table)

    def _make_or_load_pruning_table(
        self,
        table_name: str,
        constructor: Callable[..., BitpackedArray],
        constructor_kwargs: dict[str, Any],
    ) -> None:
        table_path = self.cache_path / f"{table_name}.bin"
        if table_path.exists():
            table = BitpackedArray.frombytes(table_path.read_bytes())
        else:
            table = constructor(**constructor_kwargs)
            table_path.write_bytes(table.tobytes())
        setattr(self, table_name, table)

    def load_tables(self) -> None:
        for coord, max_val, constructor in self._move_tables:
            self._make_or_load_table(
                table_name=f"{coord}_move",
                dtype=max_val_to_dtype(max_val),
                constructor=constructor,
            )

        self._make_or_load_table(
            table_name="move_conj",
            dtype=dtypes.u8,
            constructor=generators.make_move_conj_table,
        )

        for coord, max_val, constructor in self._conj_tables:
            self._make_or_load_table(
                table_name=f"{coord}_conj",
                dtype=max_val_to_dtype(max_val),
                constructor=getattr(generators, f"make_{coord}_conj_table"),
            )

        for coord, num_classes, max_val, constructor in self._sym_tables:
            table_names = (
                f"{coord}_class_lookup",
                f"{coord}_symmetry_lookup",
                f"{coord}_representative_lookup",
            )
            if all(
                (self.cache_path / f"{table_name}.bin").exists()
                for table_name in table_names
            ):
                dtypes_ = (
                    max_val_to_dtype(num_classes),
                    dtypes.u8,
                    max_val_to_dtype(max_val),
                )
                tables = []
                for table_name, dtype in zip(table_names, dtypes_):
                    table = array.array(dtype)
                    table.frombytes(
                        (self.cache_path / f"{table_name}.bin").read_bytes()
                    )
                    tables.append(table)
            else:
                tables = constructor()
                for table_name, table in zip(table_names, tables):
                    (self.cache_path / f"{table_name}.bin").write_bytes(table.tobytes())

            for table_name, table in zip(table_names, tables):
                setattr(self, table_name, table)

        constructor_kwargs = {
            name: getattr(self, name)
            for name in (
                "twist_move",
                "flip_move",
                "ud_slice_sorted_move",
                "flip_ud_slice_class_lookup",
                "flip_ud_slice_symmetry_lookup",
                "flip_ud_slice_representative_lookup",
                "twist_conj",
            )
        }
        self._make_or_load_pruning_table(
            table_name="flip_ud_slice_class_twist_prune",
            constructor=generators.make_flip_ud_slice_class_twist_prune_table,
            constructor_kwargs=constructor_kwargs,
        )

        constructor_kwargs = {
            name: getattr(self, name)
            for name in (
                "corner_move",
                "edge8_move",
                "corner_class_lookup",
                "corner_symmetry_lookup",
                "corner_representative_lookup",
                "edge8_conj",
            )
        }
        self._make_or_load_pruning_table(
            table_name="corner_class_edge8_prune",
            constructor=generators.make_corner_class_edge8_prune_table,
            constructor_kwargs=constructor_kwargs,
        )

        constructor_kwargs = {
            name: getattr(self, name)
            for name in ("corner_move", "ud_slice_sorted_move")
        }
        self._make_or_load_table(
            table_name="cornslice_prune",
            dtype=dtypes.u16,
            constructor=lambda: generators.make_cornslice_prune_table(
                **constructor_kwargs
            ),
        )

        self._make_or_load_table(
            table_name="edge_merge",
            dtype=dtypes.u16,
            constructor=generators.make_edge_merge_table,
        )
        self._make_or_load_table(
            table_name="depth_lookup",
            dtype=dtypes.u8,
            constructor=generators.make_depth_lookup_table,
        )
