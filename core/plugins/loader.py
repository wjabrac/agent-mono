import hashlib
import importlib.util
import os
import sys
from types import ModuleType
from typing import Iterable

from core.tools.registry import ToolSpec, register

def _module_name(path: str) -> str:
    """Generate a unique module name for a plugin entry path.

    Incorporates a hash of the directory to avoid collisions when multiple
    plugins share the same entry filename.
    """
    abspath = os.path.abspath(path)
    dirpath = os.path.dirname(abspath)
    base = os.path.splitext(os.path.basename(abspath))[0]
    digest = hashlib.sha1(dirpath.encode("utf-8")).hexdigest()[:8]
    return f"_plugin_{base}_{digest}"


def _load_module(path: str) -> ModuleType:
    """Load a module from ``path`` with an isolated name.

    Any previously loaded module under the same generated name is removed from
    ``sys.modules`` to support hot reloading.
    """
    mod_name = _module_name(path)
    if mod_name in sys.modules:
        del sys.modules[mod_name]
    spec = importlib.util.spec_from_file_location(mod_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load spec for {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[mod_name] = module
    spec.loader.exec_module(module)
    return module


def load_plugin(entry_path: str) -> None:
    """Load a plugin module from ``entry_path`` and register any ToolSpecs."""
    mod = _load_module(entry_path)
    for obj in mod.__dict__.values():
        if isinstance(obj, ToolSpec):
            register(obj)


def load_plugins_from_dir(directory: str, entry: str = "entry.py") -> None:
    """Load plugins from a single directory.

    This is a convenience wrapper around :func:`load_plugins_from_dirs` for the
    common case where only one plugin directory needs to be scanned.
    """
    load_plugins_from_dirs([directory], entry)


def load_plugins_from_dirs(dirs: Iterable[str], entry: str = "entry.py") -> None:
    """Load plugins from a collection of directories.

    Each directory is expected to contain the plugin entry file specified by
    ``entry`` (default ``entry.py").
    """
    for d in dirs:
        path = os.path.join(d, entry)
        if os.path.exists(path):
            load_plugin(path)
