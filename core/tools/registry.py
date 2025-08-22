"""In-memory registry for agent tools."""

from __future__ import annotations
import importlib
import importlib.util
import inspect
import os
import pkgutil
import warnings
from typing import Dict, Any, Callable, Type, Optional, List

from pydantic import BaseModel

# --- observability (optional) ---
try:
    from opentelemetry import trace as _trace  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - optional

    class _NoSpan:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def set_attribute(self, *args, **kwargs):  # pragma: no cover - no-op
            pass

    class _NoTracer:
        def start_as_current_span(self, *args, **kwargs):  # pragma: no cover - no-op
            return _NoSpan()

    _trace = type("trace", (), {"get_tracer": lambda *a, **k: _NoTracer()})()  # type: ignore

try:
    from core.observability import metrics as _metrics  # type: ignore
except Exception:  # pragma: no cover - optional
    _metrics = None  # type: ignore
try:
    from core.observability.metrics import record_tool_request  # type: ignore
except Exception:  # pragma: no cover - optional

    def record_tool_request(*args, **kwargs):  # type: ignore
        return None


_tracer = _trace.get_tracer("core.tools.registry", "0.1.0")  # no-op if shimmed


class ToolSpec(BaseModel):
    """Specification for a tool runnable by the agent."""

    name: str
    input_model: Optional[Type[BaseModel]] = None
    output_model: Optional[Type[BaseModel]] = None
    run: Callable[[Dict[str, Any]], Dict[str, Any]]


_REGISTRY: Dict[str, ToolSpec] = {}


# Expose the in-memory map via metrics.registry for tests that probe existence
class _RegistryWrapper:
    """Proxy exposing the registry for metric instrumentation."""

    def get(self, name: str) -> ToolSpec:
        """Retrieve a tool specification by name."""
        return _REGISTRY[name]


if _metrics is not None:
    _metrics.registry = _RegistryWrapper()


def names() -> List[str]:
    """Return names of all registered tools."""

    return list(_REGISTRY.keys())


def register(tool: ToolSpec) -> None:
    """Register a tool specification with the global registry."""

    with _tracer.start_as_current_span("tool.register") as span:
        span.set_attribute("tool.name", tool.name)
        prev = _REGISTRY.get(tool.name)
        if prev is not None:
            warnings.warn(f"duplicate tool registration: {tool.name}", UserWarning)
        _REGISTRY[tool.name] = tool
        try:
            record_tool_request("tool_registered", {"tool.name": tool.name})
        except Exception:  # pragma: no cover - optional metrics
            pass


def get(name: str) -> ToolSpec:
    """Retrieve a registered tool specification by name."""

    with _tracer.start_as_current_span("tool.get") as span:
        span.set_attribute("tool.name", name)
        exists = name in _REGISTRY
        try:
            record_tool_request(name, exists)
        except Exception:  # pragma: no cover - optional metrics
            pass
        span.set_attribute("tool.found", exists)
        if not exists:
            raise KeyError(f"tool not found: {name}")
        return _REGISTRY[name]


def discover(package: str = "plugins") -> None:
    """Import modules to register tools from a package or directory."""

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
        try:
            pkg = importlib.import_module(package)
        except ModuleNotFoundError:
            return
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
    """Record a discovery error during tool loading."""

    with _tracer.start_as_current_span("discovery.error") as span:
        span.set_attribute("module", mod_name)
        span.set_attribute("error.type", type(error).__name__)
        span.set_attribute("error.msg", str(error))
