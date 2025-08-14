from pathlib import Path
import shutil
import sqlite3
import pytest

from core.loader import PluginLoader
from core.safety import permissions, executor, audit


def setup_plugin(tmp_path):
    shutil.copytree(Path("core/plugins/echo"), tmp_path / "echo")
    loader = PluginLoader()
    plugin = loader.load(tmp_path / "echo")
    checker = permissions.PermissionChecker()
    checker.register_plugin(plugin.manifest.name, set(plugin.manifest.scopes_allow), plugin.manifest.rate_limit_per_min)
    con = sqlite3.connect(audit.DB_PATH)
    con.execute("DELETE FROM rate_counters")
    con.commit()
    con.close()
    return plugin, executor.Executor(checker)


def test_path_traversal_denied(tmp_path):
    plugin, exe = setup_plugin(tmp_path)
    with pytest.raises(PermissionError):
        exe.execute(plugin, "write", {"path": "../bad"}, actor="u")


def test_absolute_denied(tmp_path):
    plugin, exe = setup_plugin(tmp_path)
    with pytest.raises(PermissionError):
        exe.execute(plugin, "write", {"path": "/tmp/x"}, actor="u")


def test_cleanup(tmp_path):
    plugin, exe = setup_plugin(tmp_path)
    res = exe.execute(plugin, "write", {"path": "ok"}, actor="u")
    file_path = Path(res["written"])
    assert file_path.exists() is False


def test_network_blocked(tmp_path):
    plugin, exe = setup_plugin(tmp_path)
    with pytest.raises(PermissionError):
        exe.execute(plugin, "net", {}, actor="u")
