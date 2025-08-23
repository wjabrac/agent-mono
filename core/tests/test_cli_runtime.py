import json
import os
import subprocess
from pathlib import Path
import os
import types

import pytest

from agent_mono.cli import run_agent, EXIT_SANDBOX_ERROR

REPO_ROOT = Path(__file__).resolve().parents[2]


def run_cli(args, env=None):
    env = {**os.environ, **(env or {})}
    return subprocess.run([
        "agent",
        *args,
    ], cwd=REPO_ROOT, text=True, capture_output=True, env=env)


def test_cli_success():
    proc = run_cli(["hello"])
    assert proc.returncode == 0
    data = json.loads(proc.stdout)
    assert data["instruction"] == "hello"
    assert isinstance(data.get("tools"), list)
    assert proc.stdout.count("\n") <= 1
    assert "discovered" in proc.stderr


def test_cli_dry_run():
    proc = run_cli(["--dry-run", "hello"])
    assert proc.returncode == 0
    data = json.loads(proc.stdout)
    assert data.get("dry_run") is True
    assert data.get("tools") == []
    assert "discovered" not in proc.stderr


def test_cli_policy_denial(tmp_path):
    p = tmp_path / "policy.json"
    p.write_text(json.dumps({
        "version": 1,
        "capabilities": {
            "plugins.load": {"default": "allow"},
            "plan.generate": {"default": "allow"},
            "plan.execute": {"default": "deny"},
        },
    }))
    proc = run_cli(["--policy", str(p), "hello"])
    assert proc.returncode == 2
    data = json.loads(proc.stdout)
    assert "plan.execute" in data.get("error", "")


def test_cli_windows_no_sandbox(monkeypatch, capsys):
    import core.security.sandbox as s
    fake_os = types.SimpleNamespace(name="nt", getenv=os.getenv)
    monkeypatch.setattr(s, "os", fake_os)
    code = run_agent("hello")
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert code == EXIT_SANDBOX_ERROR
    assert "sandbox" in data.get("error", "")
