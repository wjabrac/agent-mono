import time

import pytest

from core.security import sandbox
from core.security.sandbox import SandboxTimeout


def _sleep(args):
    time.sleep(2)


def test_sandbox_timeout():
    with pytest.raises(SandboxTimeout):
        sandbox.run_in_sandbox(_sleep, {}, timeout_s=0.1)


def _echo(args):
    return {"ok": True}


def test_sandbox_runs_function():
    assert sandbox.run_in_sandbox(_echo, {}, timeout_s=1) == {"ok": True}


def test_sandbox_unsupported_os(monkeypatch):
    monkeypatch.setattr(sandbox.os, "name", "nt")
    with pytest.raises(RuntimeError):
        sandbox.run_in_sandbox(_echo, {})
