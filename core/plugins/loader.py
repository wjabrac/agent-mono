import os
import json
import importlib.util
import threading
import inspect
from typing import Dict, Any, List
from pydantic import BaseModel, ValidationError

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


def _load_module(path: str):
    spec = importlib.util.spec_from_file_location(os.path.splitext(os.path.basename(path))[0], path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load module from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    return module


def _register_from_module(module) -> None:
    from core.tools.registry import register, ToolSpec
    for _, obj in inspect.getmembers(module):
        if isinstance(obj, ToolSpec):
            register(obj)


def discover_plugins(root: str = "plugins") -> None:
    """Recursively discover plugin.json manifests under ``root`` and load entry modules."""
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
                module = _load_module(entry_path)
                _register_from_module(module)
                _loaded[manifest_path] = mtime
            except (IOError, ValidationError, Exception) as e:
                _log_error(manifest_path, e)
                continue
