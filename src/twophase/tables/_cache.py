from importlib.resources import files
from pathlib import Path
from typing import cast


def resolve_cache_path(path: str | Path | None) -> Path:
    """
    Cast supplied cache path to pathlib.Path, or default to internal cache and make
    sure directory exists.
    """
    if path is not None:
        path = Path(path)
        if path.is_file():
            raise ValueError("Cache path must be a directory...")
    else:
        path = cast(Path, files("twophase")) / "tables" / ".cache"
    path.mkdir(parents=True, exist_ok=True)
    return path
