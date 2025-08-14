"""Utilities for loading tool plugins.

This package provides helpers to discover modules in the top-level
``plugins`` package and register any `ToolSpec` instances they expose.
"""

from .loader import load_plugins

__all__ = ["load_plugins"]
