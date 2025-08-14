import importlib, pkgutil, inspect, os
from typing import Dict, Any, Callable, Type
from pydantic import BaseModel
class ToolSpec(BaseModel):
    name: str
    input_model: Type[BaseModel] | None = None
    run: Callable[[Dict[str, Any]], Dict[str, Any]] | Callable[..., Any]
_REGISTRY: Dict[str, ToolSpec] = {}

def register(tool: ToolSpec) -> None:
    _REGISTRY[tool.name] = tool

def get(name: str) -> ToolSpec:
    if name not in _REGISTRY: raise KeyError(f"tool not found: {name}")
    return _REGISTRY[name]

def discover(package: str = "plugins") -> None:
    # optional: auto-load MCP adapter
    if os.getenv("ENABLE_MCP", "true").lower() in ("1","true","yes"):
        try:
            import core.tools.mcp_adapter  # noqa: F401
        except Exception:
            pass
    pkg = importlib.import_module(package)
    for _, modname, _ in pkgutil.iter_modules(pkg.__path__):
        mod = importlib.import_module(f"{package}.{modname}")
        for _, obj in inspect.getmembers(mod):
            if isinstance(obj, ToolSpec):
                register(obj)
