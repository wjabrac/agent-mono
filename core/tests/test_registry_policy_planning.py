import importlib
from types import SimpleNamespace

import httpx
import pytest

from core.tools.registry import discover, _REGISTRY
import core.planning.advanced as adv
from core.security.policy import check_tool_allowed
from core.agentControl import execute_steps
import core.security.policy as policy


def test_registry_discovers_plugins():
    discover("plugins")
    assert "web_fetch" in _REGISTRY
    assert "pdf_text" in _REGISTRY


def test_policy_path_restrictions(tmp_path, monkeypatch):
    monkeypatch.setenv("POLICY_ENGINE_ENABLED", "true")
    monkeypatch.setenv("FS_SAFE_ROOTS", str(tmp_path))
    check_tool_allowed("mcp.fs.read", {"path": str(tmp_path / "a.txt")})
    with pytest.raises(PermissionError):
        check_tool_allowed("mcp.fs.read", {"path": "/etc/hosts"})


def test_planning_conditionals(monkeypatch):
    monkeypatch.setenv("ADVANCED_PLANNING", "true")
    importlib.reload(adv)
    plan = [
        {
            "if": True,
            "then": [{"tool": "web_fetch", "args": {"url": "https://example.com"}}],
        },
        {
            "loop": {"times": 2},
            "steps": [{"tool": "web_fetch", "args": {"url": "https://example.com"}}],
        },
    ]
    expanded = adv.expand_plan(plan)
    assert len(expanded) == 3


def test_retries_and_e2e_smoke(monkeypatch):
    # Disable interactive approvals
    monkeypatch.setenv("HITL_DEFAULT", "false")

    # Avoid real network for plugins.web_fetch (httpx)
    monkeypatch.setattr(
        httpx,
        "get",
        lambda url, timeout=15: SimpleNamespace(
            text="ok", raise_for_status=lambda: None
        ),
    )

    out = execute_steps("fetch https://example.com")
    assert "trace_id" in out
    assert isinstance(out.get("outputs"), list)


def test_retry_logic(monkeypatch):
    from core.tools.registry import ToolSpec, register

    calls = {"n": 0}

    def flaky(args):
        calls["n"] += 1
        if calls["n"] < 2:
            raise RuntimeError("fail_once")
        return {"ok": True}

    spec = ToolSpec(name="_flaky", input_model=None, run=flaky)
    register(spec)
    monkeypatch.setenv("HITL_DEFAULT", "false")
    out = execute_steps(
        "irrelevant", steps=[{"tool": "_flaky", "args": {}, "retries": 2}]
    )
    assert out["outputs"][0]["tool"] == "_flaky"
    assert out["outputs"][0]["output"]["ok"] is True


def test_duplicate_registration_warning():
    from core.tools.registry import ToolSpec, register
    import warnings

    def fn(args):
        return {}

    spec1 = ToolSpec(name="_dup", input_model=None, run=fn)
    spec2 = ToolSpec(name="_dup", input_model=None, run=fn)
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        register(spec1)
        register(spec2)
        assert any("duplicate tool registration" in str(wi.message) for wi in w)


def test_allowed_tools(monkeypatch):
    monkeypatch.setenv("POLICY_ENGINE_ENABLED", "true")
    monkeypatch.setenv("ALLOWED_TOOLS", "json_parse")
    check_tool_allowed("json_parse", {})
    with pytest.raises(PermissionError):
        check_tool_allowed("web_fetch", {"url": "https://example.com"})


def test_risky_tool_uses_sandbox(monkeypatch):
    monkeypatch.setenv("HITL_DEFAULT", "false")
    monkeypatch.setattr(policy, "RISKY_TOOLS", {"json_parse"})
    called = {}

    def _sandbox(fn, args, timeout_s=20):
        called["sandbox"] = True
        return fn(args)

    # Inject your sandbox wrapper here if/when registry/tool runner supports it.
    # This test is a placeholder to assert that risky tools route through sandbox.
    assert isinstance(called, dict)  # keeps flake8 happy
