import json, os, importlib, importlib.util, inspect
from typing import Dict, Any, List, Iterable
from core.tools.registry import register, ToolSpec, _REGISTRY

# Track loaded manifests and tools they registered
_loaded: Dict[str, Dict[str, Any]] = {}

def _iter_manifest_files(paths: Iterable[str]) -> List[str]:
    files: List[str] = []
    for p in paths:
        if not p:
            continue
        if os.path.isdir(p):
            for fname in os.listdir(p):
                if fname.endswith('.json'):
                    files.append(os.path.join(p, fname))
        else:
            files.append(p)
    return files

def _load_module_from_path(path: str):
    name = f"_plugin_{abs(hash(path))}"  # simple unique name
    spec = importlib.util.spec_from_file_location(name, path)
    if not spec or not spec.loader:
        return None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore
    return mod

def _register_from_module(mod) -> List[str]:
    names: List[str] = []
    for _, obj in inspect.getmembers(mod):
        if isinstance(obj, ToolSpec):
            register(obj)
            names.append(obj.name)
    return names

def _parse_manifest(path: str) -> List[str]:
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f) or {}
    except Exception:
        return []
    entries = data.get('plugins') or data.get('tools') or []
    loaded: List[str] = []
    for ent in entries:
        mod = None
        if isinstance(ent, str):
            try:
                mod = importlib.import_module(ent)
            except Exception:
                continue
        elif isinstance(ent, dict):
            module_name = ent.get('module')
            if module_name:
                try:
                    mod = importlib.import_module(module_name)
                except Exception:
                    continue
            else:
                path = ent.get('path')
                if path:
                    mod = _load_module_from_path(path)
        if mod is not None:
            loaded.extend(_register_from_module(mod))
    return loaded

def discover_plugins(*paths: str) -> None:
    """Discover plugins described by manifest files.

    Each argument may be a file path or directory containing ``*.json`` files.
    For each manifest file, tools defined in modules listed within are
    registered with the core tool registry. Previously loaded manifests are
    tracked so that if a manifest disappears, the tools it registered are
    removed from ``core.tools.registry._REGISTRY``.
    """
    # Determine which manifest files currently exist
    manifest_files = _iter_manifest_files(paths or [os.getenv('PLUGIN_MANIFEST_PATH', '')])
    existing = {p for p in manifest_files if os.path.exists(p)}

    # Remove manifests that no longer exist
    removed = set(_loaded.keys()) - existing
    for mp in removed:
        info = _loaded.pop(mp, {})
        for t in info.get('tools', []):
            _REGISTRY.pop(t, None)

    # Load new or changed manifests
    for mp in existing:
        try:
            mtime = os.path.getmtime(mp)
        except OSError:
            continue
        prev = _loaded.get(mp)
        if prev and prev.get('mtime') == mtime:
            continue
        prev_tools = prev.get('tools', []) if prev else []
        tools = _parse_manifest(mp)
        # remove tools no longer present
        for t in set(prev_tools) - set(tools):
            _REGISTRY.pop(t, None)
        _loaded[mp] = {"mtime": mtime, "tools": tools}
