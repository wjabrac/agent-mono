from pathlib import Path
import shutil
import sqlite3

from core.loader import PluginLoader
from core.safety.permissions import PermissionChecker
from core.safety import audit


def test_permission_scopes(tmp_path):
    shutil.copytree(Path("core/plugins/echo"), tmp_path / "echo")
    loader = PluginLoader()
    plugin = loader.load(tmp_path / "echo")
    checker = PermissionChecker()
    checker.register_plugin(plugin.manifest.name, set(plugin.manifest.scopes_allow), plugin.manifest.rate_limit_per_min)
    con = sqlite3.connect(audit.DB_PATH)
    con.execute("DELETE FROM rate_counters")
    con.commit()
    con.close()

    allow = checker.check("echo", "write", "u", {"fs.temp"})
    deny = checker.check("echo", "write", "u", {"fs.read"})
    assert allow.allowed is True
    assert deny.allowed is False
