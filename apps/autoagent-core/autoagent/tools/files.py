from __future__ import annotations
"""Convenience wrappers for file-related tools.

These functions provide a simplified interface that accepts an optional
``env`` argument and forwards to the underlying implementations in
``terminal_tools`` using the ``code_env`` context variable.  Tests and other
callers that previously imported from ``autoagent.tools.files`` can continue to
work without needing to construct the context dictionary manually.
"""
from typing import Optional, Dict

from .terminal_tools import (
    create_file as _create_file,
    write_file as _write_file,
    read_file as _read_file,
    list_files as _list_files,
    create_directory as _create_directory,
)


def _context(env: Optional[object]) -> Dict[str, object]:
    return {"code_env": env} if env is not None else {}


def create_file(path: str, content: str, env: Optional[object] = None) -> str:
    """Create a file at ``path`` with ``content``.

    Args:
        path: Destination path for the file.
        content: Text content to write.
        env: Optional execution environment.
    """
    return _create_file(path, content, _context(env))


def write_file(path: str, content: str, env: Optional[object] = None) -> str:
    """Write ``content`` to an existing file at ``path``."""
    return _write_file(path, content, _context(env))


def read_file(path: str, env: Optional[object] = None) -> str:
    """Read and return the contents of ``path``."""
    return _read_file(path, _context(env))


def list_files(path: str, env: Optional[object] = None) -> str:
    """List files under ``path``."""
    return _list_files(path, _context(env))


def create_directory(path: str, env: Optional[object] = None) -> str:
    """Create a directory at ``path``."""
    return _create_directory(path, _context(env))
