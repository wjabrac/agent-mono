import sqlite3
from pathlib import Path
import shutil

from core.loader import PluginLoader
from core.safety import permissions, executor, audit


def test_audit_records(tmp_path):
    db_path = audit.DB_PATH
    if db_path.exists():
        con = sqlite3.connect(db_path)
        con.execute("DELETE FROM audit_events")
        con.execute("DELETE FROM rate_counters")
        con.commit()
        con.close()
    shutil.copytree(Path("core/plugins/echo"), tmp_path / "echo")
    loader = PluginLoader()
    plugin = loader.load(tmp_path / "echo")
    checker = permissions.PermissionChecker()
    checker.register_plugin(plugin.manifest.name, set(plugin.manifest.scopes_allow), 1)
    exe = executor.Executor(checker)
    exe.execute(plugin, "write", {"path": "a"}, actor="u")
    exe.execute(plugin, "write", {"path": "b"}, actor="u")
    con = sqlite3.connect(db_path)
    cur = con.execute("SELECT decision, rate_limited FROM audit_events ORDER BY id")
    rows = cur.fetchall()
    con.close()
    assert rows[0][0] == "allow"
    assert rows[1][0] == "deny" and rows[1][1] == 1
