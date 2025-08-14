import importlib, pkgutil, inspect, os, json, time, threading, sys, types
from typing import Dict, Any, Callable, Type, List
from pydantic import BaseModel
from core.observability.trace import log_event
from core.tools.manifest import ensure_tool_entry

class ToolSpec(BaseModel):
    name: str
    input_model: Type[BaseModel] | None = None
    run: Callable[[Dict[str, Any]], Dict[str, Any]] | Callable[..., Any]

_REGISTRY: Dict[str, ToolSpec] = {}
_DISCOVERED_PACKAGES: List[str] = []
_HOT_RELOAD = os.getenv("TOOL_HOT_RELOAD", "false").lower() in ("1","true","yes")
_REMOTE_CONFIG_PATH = os.getenv("REMOTE_TOOLS_CONFIG", "")
_MICROTOOL_DIRS = [p for p in os.getenv("MICROTOOL_DIRS", "tools").split(":") if p]
_last_load_ts = 0.0
_lock = threading.Lock()


def register(tool: ToolSpec) -> None:
    _REGISTRY[tool.name] = tool


def get(name: str) -> ToolSpec:
    if name not in _REGISTRY: raise KeyError(f"tool not found: {name}")
    return _REGISTRY[name]


def _load_remote_tools_from_config() -> None:
    if not _REMOTE_CONFIG_PATH or not os.path.exists(_REMOTE_CONFIG_PATH):
        return
    try:
        from core.tools.remote import RemoteToolConfig, build_remote_tool
        with open(_REMOTE_CONFIG_PATH, "r", encoding="utf-8") as f:
            cfg = json.load(f)
        tools = cfg if isinstance(cfg, list) else cfg.get("tools", [])
        for item in tools:
            try:
                spec = build_remote_tool(RemoteToolConfig(**item))
                register(spec)
            except Exception:
                continue
    except Exception:
        pass


def _do_discover(package: str) -> None:
    pkg = importlib.import_module(package)
    for _, modname, _ in pkgutil.iter_modules(pkg.__path__):
        mod = importlib.import_module(f"{package}.{modname}")
        for _, obj in inspect.getmembers(mod):
            if isinstance(obj, ToolSpec):
                register(obj)


def _discover_microtools_from_dirs() -> None:
    # Discover any python files in configured directories and import them.
    for root in _MICROTOOL_DIRS:
        if not root:
            continue
        if not os.path.isdir(root):
            continue
        sys.path.insert(0, os.path.abspath("."))
        for fname in os.listdir(root):
            if not fname.endswith(".py") or fname.startswith("_"):
                continue
            mod_path = os.path.splitext(fname)[0]
            full_mod = f"{root.replace('/', '.').strip('.')}.{mod_path}" if root != "." else mod_path
            try:
                mod = importlib.import_module(full_mod)
            except Exception:
                continue
            # Identify functions decorated with @microtool
            for _, fn in inspect.getmembers(mod, inspect.isfunction):
                mt = getattr(fn, "_microtool_spec", None)
                if mt is None:
                    continue
                try:
                    from core.tools.microtool import build_toolspec_from_microtool
                    spec = build_toolspec_from_microtool(fn)
                    register(spec)
                    # update manifest path
                    file_path = os.path.join(root, fname)
                    ensure_tool_entry(mt.name, path=file_path, tags=mt.tags, composite_of=[], description=mt.description)
                except Exception:
                    continue


def discover(package: str = "plugins") -> None:
    # optional: auto-load MCP adapter
    if os.getenv("ENABLE_MCP", "true").lower() in ("1","true","yes"):
        try:
            import core.tools.mcp_adapter  # noqa: F401
        except Exception:
            pass
    with _lock:
        if package:
            _do_discover(package)
            _DISCOVERED_PACKAGES.append(package)
        _discover_microtools_from_dirs()
        _load_remote_tools_from_config()
        global _last_load_ts
        _last_load_ts = time.time()


def reload_if_needed() -> None:
    if not _HOT_RELOAD:
        return
    global _last_load_ts
    try:
        mtime = os.path.getmtime(_REMOTE_CONFIG_PATH) if _REMOTE_CONFIG_PATH else 0
    except Exception:
        mtime = 0
    if mtime and mtime > _last_load_ts:
        with _lock:
            _load_remote_tools_from_config(); _last_load_ts = time.time()
    # Re-import plugin modules and microtool modules
    for pkg in list(set(_DISCOVERED_PACKAGES)):
        try:
            _do_discover(pkg)
        except Exception:
            continue
    _discover_microtools_from_dirs()
