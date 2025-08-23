import json
from pathlib import Path

from agent_mono import policy


def test_load_valid(tmp_path):
    p = tmp_path / "pol.json"
    p.write_text(json.dumps({"version": 1, "capabilities": {"plan.execute": {"default": "allow"}}}))
    policy.load(str(p))
    assert policy.allow("plan.execute")
    snap = policy.snapshot()
    assert snap.get("path", "").endswith("pol.json")


def test_missing_file_default_deny(tmp_path):
    missing = tmp_path / "missing.json"
    policy.load(str(missing))
    assert not policy.allow("network")
    assert "path" not in policy.snapshot()


def test_invalid_file_default_deny(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text("{")
    policy.load(str(bad))
    assert not policy.allow("network")
    assert "path" not in policy.snapshot()
