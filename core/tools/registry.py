import importlib, pkgutil, inspect, os, json, time, threading
from typing import Dict, Any, Callable, Type, List
from pydantic import BaseModel
from core.observability.trace import log_event

class ToolSpec(BaseModel):
    name: str
    input_model: Type[BaseModel] | None = None
    run: Callable[[Dict[str, Any]], Dict[str, Any]] | Callable[..., Any]

_REGISTRY: Dict[str, ToolSpec] = {}
_DISCOVERED_PACKAGES: List[str] = []
_HOT_RELOAD = os.getenv("TOOL_HOT_RELOAD", "false").lower() in ("1","true","yes")
_REMOTE_CONFIG_PATH = os.getenv("REMOTE_TOOLS_CONFIG", "")
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


def discover(package: str = "plugins") -> None:
    # optional: auto-load MCP adapter
    if os.getenv("ENABLE_MCP", "true").lower() in ("1","true","yes"):
        try:
            import core.tools.mcp_adapter  # noqa: F401
        except Exception:
            pass
    with _lock:
        _do_discover(package)
        _DISCOVERED_PACKAGES.append(package)
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
    # Re-import plugin modules to support hot plugging (best-effort)
    for pkg in list(set(_DISCOVERED_PACKAGES)):
        try:
            _do_discover(pkg)
        except Exception:
            continue
