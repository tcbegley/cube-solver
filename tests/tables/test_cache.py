from importlib.resources import files
from pathlib import Path
from tempfile import NamedTemporaryFile, TemporaryDirectory
from typing import cast

import pytest

from twophase.tables._cache import resolve_cache_path


def test_resolve_default_cache_path():
    resolved_path = resolve_cache_path(None)
    assert isinstance(resolved_path, Path)
    assert resolved_path.exists()
    assert resolved_path.is_dir()
    assert resolved_path.is_relative_to(
        cast(Path, files("twophase")) / "tables" / ".cache"
    )


def resolve_str_cache_path():
    with TemporaryDirectory() as tempdir:
        resolved_path = resolve_cache_path(tempdir)
        assert isinstance(resolved_path, Path)
        assert resolved_path.exists()
        assert resolved_path.is_dir()
        assert resolved_path.is_relative_to(Path(tempdir))


def resolve_pathlib_cache_path():
    with TemporaryDirectory() as tempdir:
        tempdir = Path(tempdir)
        resolved_path = resolve_cache_path(tempdir)
        assert isinstance(resolved_path, Path)
        assert resolved_path.exists()
        assert resolved_path.is_dir()
        assert resolved_path.is_relative_to(Path(tempdir))


def raises_value_error():
    with pytest.raises(ValueError), NamedTemporaryFile() as tempfile:
        resolve_cache_path(str(tempfile))
