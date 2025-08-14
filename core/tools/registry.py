import importlib, pkgutil, inspect
from typing import Dict, Any, Callable, Type
from pydantic import BaseModel

from core.observability.metrics import record_tool_request
class ToolSpec(BaseModel):
    name: str
    input_model: Type[BaseModel]
    run: Callable[[Dict[str, Any]], Dict[str, Any]]
_REGISTRY: Dict[str, ToolSpec] = {}
def register(tool: ToolSpec) -> None:
    _REGISTRY[tool.name] = tool
def get(name: str) -> ToolSpec:
    if name not in _REGISTRY:
        record_tool_request(name, "not_found")
        raise KeyError(f"tool not found: {name}")
    record_tool_request(name, "found")
    return _REGISTRY[name]
def discover(package: str = "plugins") -> None:
    pkg = importlib.import_module(package)
    for _, modname, _ in pkgutil.iter_modules(pkg.__path__):
        mod = importlib.import_module(f"{package}.{modname}")
        for _, obj in inspect.getmembers(mod):
            if isinstance(obj, ToolSpec):
                register(obj)
