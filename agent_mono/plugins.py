"""Entry-point based plugin loader with lazy imports."""
from importlib.metadata import entry_points, EntryPoint
from typing import Dict, Any

GROUP = "agent_mono.plugins"

def list_plugins() -> Dict[str, EntryPoint]:
    """Return a mapping of plugin names to their entry points."""
    return {ep.name: ep for ep in entry_points(group=GROUP)}

def load_plugin(name: str) -> Any:
    """Load a plugin object by name without importing others."""
    ep = list_plugins()[name]
    return ep.load()

def run_plugin(name: str, **kw: Any) -> Any:
    """Load the named plugin and execute it with provided keywords."""
    plugin = load_plugin(name)
    run = getattr(plugin, "run", plugin)
    return run(**kw)

__all__ = ["GROUP", "list_plugins", "load_plugin", "run_plugin"]
