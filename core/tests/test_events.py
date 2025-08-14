from pathlib import Path
import shutil

from core.loader import PluginLoader
from core.safety import events, permissions, executor


def test_event_order(tmp_path):
    shutil.copytree(Path("core/plugins/echo"), tmp_path / "echo")
    order = []
    events.on("on_plugin_load", lambda p: order.append("load"))
    events.on("before_command", lambda *a: order.append("before"))
    events.on("after_command", lambda *a: order.append("after"))

    loader = PluginLoader()
    plugin = loader.load(tmp_path / "echo")
    checker = permissions.PermissionChecker()
    checker.register_plugin(plugin.manifest.name, set(plugin.manifest.scopes_allow), plugin.manifest.rate_limit_per_min)
    exe = executor.Executor(checker)
    exe.execute(plugin, "write", {"path": "a.txt"}, actor="u")
    assert order == ["load", "before", "after"]
