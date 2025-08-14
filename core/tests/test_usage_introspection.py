import json
import os
from importlib import reload
from tempfile import TemporaryDirectory


def test_usage_and_introspection(monkeypatch):
    with TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "usage.db")
        manifest_path = os.path.join(tmpdir, "manifest.json")
        monkeypatch.setenv("AGENT_USAGE_DB", db_path)
        monkeypatch.setenv("TOOLS_MANIFEST_PATH", manifest_path)
        import core.tools.manifest as manifest_module
        reload(manifest_module)
        from core import usage_db
        reload(usage_db)
        from core.usage_db import log_run
        import plugins.introspect as introspect
        reload(introspect)
        manifest = {
            "used": {"uses": 1, "errors": 0, "path": "", "tags": [], "composite_of": [], "description": "", "last_used": 0},
            "unused": {"uses": 0, "errors": 0, "path": "", "tags": [], "composite_of": [], "description": "", "last_used": 0},
        }
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f)
        log_run("cmd1", 0, 100, None)
        for _ in range(3):
            log_run("cmd2", 1, 50, "fail")
        out = introspect.spec.run({})
        assert "unused" in out["unused_plugins"]
        assert "cmd2" in out["failing_commands"]
        assert "cmd2" in out["helper_suggestions"]
