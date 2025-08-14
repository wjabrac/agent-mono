import importlib
from types import SimpleNamespace
from core.tools.registry import discover, _REGISTRY
import core.planning.advanced as adv
from core.security.policy import check_tool_allowed
from core.agentControl import execute_steps


def test_registry_discovers_plugins():
	# should discover at least built-in tools
	discover("plugins")
	assert "web_fetch" in _REGISTRY
	assert "pdf_text" in _REGISTRY


def test_policy_path_restrictions(tmp_path, monkeypatch):
	monkeypatch.setenv("POLICY_ENGINE_ENABLED", "true")
	monkeypatch.setenv("FS_SAFE_ROOTS", str(tmp_path))
	# allowed
	check_tool_allowed("mcp.fs.read", {"path": str(tmp_path / "a.txt")})
	# not allowed
	try:
		check_tool_allowed("mcp.fs.read", {"path": "/etc/hosts"})
		assert False
	except PermissionError:
		assert True


def test_planning_conditionals(monkeypatch):
	monkeypatch.setenv("ADVANCED_PLANNING", "true")
	importlib.reload(adv)
	plan = [
		{"if": True, "then": [{"tool": "web_fetch", "args": {"url": "https://example.com"}}]},
		{"loop": {"times": 2}, "steps": [{"tool": "web_fetch", "args": {"url": "https://example.com"}}]},
	]
	expanded = adv.expand_plan(plan)
	assert len(expanded) == 3


def test_retries_and_e2e_smoke(monkeypatch):
	# Disable interactive approvals
	monkeypatch.setenv("HITL_DEFAULT", "false")
	# Avoid real network: stub requests.get used by plugins.web_fetch
	import plugins.web_fetch as wf
	class _Resp:
		def __init__(self, text="ok"): self.text = text
		def raise_for_status(self): return None
	monkeypatch.setattr(wf.requests, "get", lambda url, timeout=15: _Resp("ok"))
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
	# Provide explicit steps with retries
	out = execute_steps("irrelevant", steps=[{"tool": "_flaky", "args": {}, "retries": 2}])
	assert out["outputs"][0]["tool"] == "_flaky"
	assert out["outputs"][0]["output"]["ok"] is True