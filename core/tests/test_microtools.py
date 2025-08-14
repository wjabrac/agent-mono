import os, json
from core.tools.registry import discover, get
from core.tools.manifest import load_manifest
from core.agentControl import execute_steps


def test_microtool_discovery(tmp_path, monkeypatch):
    monkeypatch.setenv("MICROTOOL_DIRS", "tools")
    discover("")
    assert get("search")
    assert get("compare")
    assert get("optimize")


def test_microtool_usage_tracking(monkeypatch):
    monkeypatch.setenv("MICROTOOL_DIRS", "tools")
    monkeypatch.setenv("TOOLS_MANIFEST_PATH", "data/tools_manifest.json")
    # avoid HITL for single step
    monkeypatch.setenv("HITL_DEFAULT", "false")
    discover("")
    out = execute_steps("compare stuff", steps=[{"tool": "compare", "args": {"a": 1, "b": 1}}])
    mf = load_manifest()
    assert "compare" in mf and mf["compare"]["uses"] >= 1


def test_microtool_composite(monkeypatch):
    monkeypatch.setenv("MICROTOOL_DIRS", "tools")
    monkeypatch.setenv("HITL_DEFAULT", "false")
    discover("")
    data = ["a", "b", "c"]
    out = execute_steps("optimize", steps=[{"tool": "optimize", "args": {"data": data, "term": "b", "cmp": "b"}}])
    res = out["outputs"][0]["output"]
    assert res["search"]["count"] == 1
    assert res["compare"]["equal"] is True


def test_sync_async_chain(monkeypatch):
    monkeypatch.setenv("MICROTOOL_DIRS", "tools")
    monkeypatch.setenv("HITL_DEFAULT", "false")
    discover("")
    steps = [
        {"tool": "search", "args": {"data": ["x"], "term": "x"}},
        {"tool": "async_echo", "args": {"msg": "ok"}},
    ]
    out = execute_steps("combo", steps=steps)
    assert out["outputs"][0]["output"]["count"] == 1
    assert out["outputs"][1]["output"]["echo"] == "ok"
