import os
import sys
import json
import hashlib
import inspect
import threading
import pkgutil
import importlib
import importlib.util
from types import ModuleType
from typing import Iterable, Dict, Any, List
from importlib import import_module

from pydantic import BaseModel, ValidationError
from core.tools.registry import ToolSpec, register

# Track loaded plugin manifests by path -> mtime
_loaded: Dict[str, float] = {}
_lock = threading.Lock()


class PluginManifest(BaseModel):
    """Schema for plugin.json files."""
    name: str
    version: str
    entry: str
    scopes: List[str] | None = None
    commands: List[str] | None = None


def _log_error(mod_name: str, error: Exception) -> None:
    # Lazy import to avoid circular dependency at module import
    from core.tools.registry import _log_discovery_error  # type: ignore
    _log_discovery_error(mod_name, error)


# -----------------------------
# Direct entry-file loading (supports plugin paths and hot reload)
# -----------------------------
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


def _load_module_from_path(path: str) -> ModuleType:
    """Load a module from path with an isolated name and hot-reload safety."""
    importlib.invalidate_caches()
    mod_name = _module_name(path)
    sys.modules.pop(mod_name, None)
    spec = importlib.util.spec_from_file_location(mod_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load spec for {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[mod_name] = module
    spec.loader.exec_module(module)
    return module


def _register_from_module(module: ModuleType) -> None:
    """Register any ToolSpec instances defined in a loaded module."""
    for _, obj in inspect.getmembers(module):
        if isinstance(obj, ToolSpec):
            register(obj)


def load_plugin(entry_path: str) -> None:
    """Load a plugin module from entry_path and register any ToolSpecs."""
    mod = _load_module_from_path(entry_path)
    _register_from_module(mod)


def load_plugins_from_dir(directory: str, entry: str = "entry.py") -> None:
    """Load plugins from a single directory by entry filename (default entry.py)."""
    load_plugins_from_dirs([directory], entry)


def load_plugins_from_dirs(dirs: Iterable[str], entry: str = "entry.py") -> None:
    """Load plugins from multiple directories by entry filename (default entry.py)."""
    for d in dirs:
        path = os.path.join(d, entry)
        if os.path.exists(path):
            load_plugin(path)


# -----------------------------
# Manifest-based recursive discovery (plugin.json)
# -----------------------------
def _load_module(path: str) -> ModuleType:
    """Legacy helper: load a module from path using its basename as module name."""
    spec = importlib.util.spec_from_file_location(
        os.path.splitext(os.path.basename(path))[0], path
    )
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load module from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    return module


def discover_plugins(root: str = "plugins") -> None:
    """Recursively discover plugin.json manifests under root and load entry modules."""
    if not os.path.isdir(root):
        return
    with _lock:
        for dirpath, _, filenames in os.walk(root):
            if "plugin.json" not in filenames:
                continue
            manifest_path = os.path.join(dirpath, "plugin.json")
            try:
                mtime = os.path.getmtime(manifest_path)
            except OSError:
                continue
            if _loaded.get(manifest_path) == mtime:
                # unchanged
                continue
            try:
                with open(manifest_path, "r", encoding="utf-8") as f:
                    data: Dict[str, Any] = json.load(f)
                manifest = PluginManifest(**data)
                entry_path = os.path.join(dirpath, manifest.entry)
                # Use hot-reload-safe loader here as well
                module = _load_module_from_path(entry_path)
                _register_from_module(module)
                _loaded[manifest_path] = mtime
            except (IOError, ValidationError, Exception) as e:
                _log_error(manifest_path, e)
                continue


# -----------------------------
# Backwards-compatible package scanning (plugins as a Python package)
# -----------------------------
def load_plugins(package: str = "plugins") -> List[str]:
    """
    Import each submodule under the given package and register a top-level `spec`
    if present.
    """
    loaded: List[str] = []
    try:
        pkg = import_module(package)
    except Exception:
        return loaded

    for _, modname, _ in pkgutil.iter_modules(pkg.__path__):
        full_name = f"{package}.{modname}"
        try:
            mod = import_module(full_name)
        except Exception as e:
            _log_error(full_name, e)
            continue
        spec = getattr(mod, "spec", None)
        if isinstance(spec, ToolSpec):
            register(spec)
            loaded.append(spec.name)
    return loaded
