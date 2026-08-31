"""An educational implementation of Kociemba's two-phase cube solver."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("twophase")
except PackageNotFoundError:
    __version__ = "0.2.0+fallback"

__all__ = ["__version__"]
