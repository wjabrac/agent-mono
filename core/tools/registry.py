from __future__ import annotations
import importlib
import importlib.util
import inspect
import os
import pkgutil
import warnings
from typing import Dict, Any, Callable, Type, Optional

from pydantic import BaseModel
from opentelemetry import trace as _trace
from core.observability import metrics as _metrics
from core.observability.metrics import record_tool_request

_tracer = _trace.get_tracer("core.tools.registry", "0.1.0")

class ToolSpec(BaseModel):
    name: str
    input_model: Optional[Type[BaseModel]] = None
    run: Callable[[Dict[str, Any]], Dict[str, Any]]

_REGISTRY: Dict[str, ToolSpec] = {}

# Expose the in-memory map via metrics.registry for tests that probe existence
class _RegistryWrapper:
    def get(self, name: str) -> ToolSpec:
        return _REGISTRY[name]

_metrics.registry = _RegistryWrapper()

def register(tool: ToolSpec) -> None:
    with _tracer.start_as_current_span("tool.register") as span:
        span.set_attribute("tool.name", tool.name)
        if tool.name in _REGISTRY:
            warnings.warn("duplicate tool registration", UserWarning)
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
        if not package:
            dirs = os.getenv("MICROTOOL_DIRS", "").split(",")
            for d in dirs:
                d = d.strip()
                if not d or not os.path.isdir(d):
                    continue
                for fname in os.listdir(d):
                    if not fname.endswith(".py") or fname.startswith("_"):
                        continue
                    path = os.path.join(d, fname)
                    mod_name = os.path.splitext(fname)[0]
                    spec = importlib.util.spec_from_file_location(mod_name, path)
                    if not spec or not spec.loader:
                        continue
                    mod = importlib.util.module_from_spec(spec)
                    try:
                        spec.loader.exec_module(mod)
                    except Exception as e:
                        _log_discovery_error(path, e)
                        continue
                    from core.tools.microtool import build_toolspec_from_microtool
                    for _, obj in inspect.getmembers(mod):
                        if isinstance(obj, ToolSpec):
                            register(obj)
                        elif callable(obj) and hasattr(obj, "_microtool_spec"):
                            register(build_toolspec_from_microtool(obj))
            return
        pkg = importlib.import_module(package)
        for _, modname, _ in pkgutil.iter_modules(pkg.__path__):
            mod_full = f"{package}.{modname}"
            try:
                mod = importlib.import_module(mod_full)
            except Exception as e:
                _log_discovery_error(mod_full, e)
                continue
            from core.tools.microtool import build_toolspec_from_microtool
            for _, obj in inspect.getmembers(mod):
                if isinstance(obj, ToolSpec):
                    register(obj)
                elif callable(obj) and hasattr(obj, "_microtool_spec"):
                    register(build_toolspec_from_microtool(obj))

def _log_discovery_error(mod_name: str, error: Exception) -> None:
    with _tracer.start_as_current_span("discovery.error") as span:
        span.set_attribute("module", mod_name)
        span.set_attribute("error.type", type(error).__name__)
        span.set_attribute("error.msg", str(error))
