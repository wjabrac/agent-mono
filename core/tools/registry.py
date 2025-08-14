import importlib, pkgutil, inspect, os, json, time, threading, sys
from typing import Dict, Any, Callable, Type, List
from pydantic import BaseModel
from core.observability.metrics import record_tool_request
from core.tools.manifest import ensure_tool_entry
from core.plugins import discover_plugins as _discover_plugins

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
    if name not in _REGISTRY:
        record_tool_request(name, "false")
        raise KeyError(f"tool not found: {name}")
    record_tool_request(name, "true")
    return _REGISTRY[name]


def _log_discovery_error(mod_name: str, error: Exception) -> None:
    try:
        from core.observability.trace import log_event, start_trace
        tid = start_trace(None)
        log_event(tid, "decision", "discovery:error", {"module": mod_name, "error": type(error).__name__, "msg": str(error)})
    except Exception:
        # fallback to stderr
        sys.stderr.write(f"[discovery:error] {mod_name}: {type(error).__name__}: {error}\n")


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
    except Exception as e:
        _log_discovery_error("remote_tools_config", e)


def _do_discover(package: str) -> None:
    try:
        pkg = importlib.import_module(package)
    except Exception as e:
        _log_discovery_error(package, e); return
    for _, modname, _ in pkgutil.iter_modules(pkg.__path__):
        try:
            mod = importlib.import_module(f"{package}.{modname}")
        except Exception as e:
            _log_discovery_error(f"{package}.{modname}", e); continue
        for _, obj in inspect.getmembers(mod):
            if isinstance(obj, ToolSpec):
                register(obj)


def _discover_microtools_from_dirs() -> None:
    # Ensure project root is present only once
    root = os.path.abspath(".")
    if root not in sys.path:
        sys.path.insert(0, root)
    for dirpath in list(_MICROTOOL_DIRS):
        if not dirpath or not os.path.isdir(dirpath):
            continue
        for fname in os.listdir(dirpath):
            if not fname.endswith(".py") or fname.startswith("_"):
                continue
            mod_path = os.path.splitext(fname)[0]
            full_mod = f"{dirpath.replace('/', '.').strip('.')}.{mod_path}" if dirpath != "." else mod_path
            try:
                mod = importlib.import_module(full_mod)
            except Exception as e:
                _log_discovery_error(full_mod, e); continue
            for _, fn in inspect.getmembers(mod, inspect.isfunction):
                mt = getattr(fn, "_microtool_spec", None)
                if mt is None:
                    continue
                try:
                    from core.tools.microtool import build_toolspec_from_microtool
                    spec = build_toolspec_from_microtool(fn)
                    register(spec)
                    # Now that we know the source file and mt metadata, record manifest entry
                    ensure_tool_entry(mt.name, path=os.path.join(dirpath, fname), tags=mt.tags, composite_of=[], description=mt.description)
                except Exception as e:
                    _log_discovery_error(full_mod, e); continue


def _discover_templates() -> None:
    path = os.getenv("TEMPLATES_PATH", "data/templates.json")
    if not os.path.exists(path):
        return
    try:
        from core.instrumentation import instrument_tool
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f) or {}
        for name, body in data.items():
            steps = body.get("steps") or []
            desc = body.get("description", "")
            # Build a thin wrapper that returns predefined steps, allowing param injection
            def _make(name, steps, desc):
                @instrument_tool(name)
                def _run(args: Dict[str, Any]) -> Dict[str, Any]:
                    from copy import deepcopy
                    # naive parameter substitution: ${var}
                    s = deepcopy(steps)
                    params = args or {}
                    import re
                    def _subst(val):
                        if isinstance(val, str):
                            for k,v in params.items():
                                val = re.sub(r"\\$\\{"+re.escape(k)+r"\\}", str(v), val)
                        return val
                    for st in s:
                        st["args"] = {k: _subst(v) for k,v in (st.get("args") or {}).items()}
                    return {"steps": s}
                return _run
            run = _make(name, steps, desc)
            register(ToolSpec(name=name, input_model=None, run=run))
            ensure_tool_entry(name, path=path, tags=["template"], composite_of=[st.get("tool") for st in steps], description=desc)
    except Exception as e:
        _log_discovery_error("templates", e); return


def discover(package: str = "plugins") -> None:
    if os.getenv("ENABLE_MCP", "true").lower() in ("1","true","yes"):
        try:
            import core.tools.mcp_adapter  # noqa: F401
        except Exception as e:
            _log_discovery_error("mcp_adapter", e)
    with _lock:
        if package:
            _do_discover(package)
            _DISCOVERED_PACKAGES.append(package)
        _discover_microtools_from_dirs()
        _discover_templates()
        _load_remote_tools_from_config()
        _discover_plugins()
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
    for pkg in list(set(_DISCOVERED_PACKAGES)):
        try:
            _do_discover(pkg)
        except Exception as e:
            _log_discovery_error(pkg, e); continue
    _discover_microtools_from_dirs()
    _discover_templates()
    _discover_plugins()
