"""Discover and register plugin ToolSpecs."""

from importlib import import_module
import pkgutil
from typing import List

from core.tools.registry import ToolSpec, register


def load_plugins(package: str = "plugins") -> List[str]:
    """Load ToolSpecs from all modules in ``package``.

    Each module under ``package`` is imported. If the module defines a
    top-level variable named ``spec`` that is an instance of ``ToolSpec``,
    it will be registered with :func:`core.tools.registry.register`.

    Parameters
    ----------
    package: str
        Package name to search. Defaults to ``"plugins"``.

    Returns
    -------
    List[str]
        Names of the tools that were registered.
    """
    loaded: List[str] = []
    try:
        pkg = import_module(package)
    except Exception:
        return loaded

    for _, modname, _ in pkgutil.iter_modules(pkg.__path__):
        full_name = f"{package}.{modname}"
        try:
            mod = import_module(full_name)
        except Exception:
            continue
        spec = getattr(mod, "spec", None)
        if isinstance(spec, ToolSpec):
            register(spec)
            loaded.append(spec.name)
    return loaded
