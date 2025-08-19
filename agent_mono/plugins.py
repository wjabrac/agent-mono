"""Entry-point based plugin loader with lazy imports."""
from importlib.metadata import entry_points, EntryPoint
from typing import Dict, Any, Mapping

GROUP = "agent_mono.plugins"

def list_plugins() -> Mapping[str, EntryPoint]:
    """Return a mapping of plugin names to their entry points."""
    return {ep.name: ep for ep in entry_points(group=GROUP)}

def load_plugin(name: str) -> Any:
    """Load a plugin object by name without importing others."""
    plugins = list_plugins()
    if name not in plugins:
        raise KeyError(f"unknown plugin {name!r}")
    ep = plugins[name]
    return ep.load()

def run_plugin(name: str, **kw: Any) -> Any:
    """Load the named plugin and execute it with provided keywords."""
    plugin = load_plugin(name)
    if not hasattr(plugin, "run"):
        raise TypeError(f"plugin {name!r} does not expose a run callable")
    return plugin.run(**kw)  # type: ignore[no-any-return]

__all__ = ["GROUP", "list_plugins", "load_plugin", "run_plugin"]
