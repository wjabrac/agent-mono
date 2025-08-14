from pathlib import Path
import shutil

from core.loader import PluginLoader
from core.safety import permissions, executor


def test_rate_limit(tmp_path):
    shutil.copytree(Path("core/plugins/echo"), tmp_path / "echo")
    loader = PluginLoader()
    plugin = loader.load(tmp_path / "echo")
    checker = permissions.PermissionChecker()
    checker.register_plugin(plugin.manifest.name, set(plugin.manifest.scopes_allow), 2)
    exe = executor.Executor(checker)
    assert exe.execute(plugin, "write", {"path": "a"}, actor="u")
    assert exe.execute(plugin, "write", {"path": "b"}, actor="u")
    res = exe.execute(plugin, "write", {"path": "c"}, actor="u")
    assert res == {"denied": "rate_limited"}
