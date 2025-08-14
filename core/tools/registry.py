from __future__ import annotations
import importlib, pkgutil, inspect
from typing import Dict, Any, Callable, Type, Optional
from pydantic import BaseModel
from opentelemetry import trace as _trace
from core.observability.metrics import record_tool_request

_tracer = _trace.get_tracer("core.tools.registry", "0.1.0")


class ToolSpec(BaseModel):
    name: str
    input_model: Optional[Type[BaseModel]] = None
    run: Callable[[Dict[str, Any]], Dict[str, Any]]


_REGISTRY: Dict[str, ToolSpec] = {}


def register(tool: ToolSpec) -> None:
    with _tracer.start_as_current_span("tool.register") as span:
        span.set_attribute("tool.name", tool.name)
        _REGISTRY[tool.name] = tool


def get(name: str) -> ToolSpec:
    with _tracer.start_as_current_span("tool.get") as span:
        span.set_attribute("tool.name", name)
        exists = name in _REGISTRY
        record_tool_request(name, exists)
        span.set_attribute("tool.found", exists)
        if not exists:
            raise KeyError(f"tool not found: {name}")
        return _REGISTRY[name]


def discover(package: str = "plugins") -> None:
    with _tracer.start_as_current_span("tools.discover") as span:
        span.set_attribute("package", package)
        pkg = importlib.import_module(package)
        for _, modname, _ in pkgutil.iter_modules(pkg.__path__):
            mod_full = f"{package}.{modname}"
            try:
                mod = importlib.import_module(mod_full)
            except Exception as e:
                with _tracer.start_as_current_span("discovery.error") as es:
                    es.set_attribute("module", mod_full)
                    es.set_attribute("error.type", type(e).__name__)
                    es.set_attribute("error.msg", str(e))
                continue
            for _, obj in inspect.getmembers(mod):
                if isinstance(obj, ToolSpec):
                    register(obj)

