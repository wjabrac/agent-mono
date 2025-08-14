import sys
import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock
import pytest
import types
import core

# Ensure the repository and service directories are on the Python path so we can import modules
SERVICE_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.append(str(SERVICE_DIR))
sys.path.append(str(REPO_ROOT))

import workflow as wf


def test_run_steps_invokes_execute_steps(monkeypatch):
    fake_exec = MagicMock(return_value={"ok": True})
    stub = types.ModuleType("agentControl")
    stub.execute_steps = fake_exec
    monkeypatch.setitem(sys.modules, "core.agentControl", stub)
    inp = wf.AgentWorkflowInput(
        prompt="p", steps=[{"tool": "t", "args": {}}], thread="th", tags=None
    )
    result = wf.run_steps(inp)
    fake_exec.assert_called_once_with(
        "p", [{"tool": "t", "args": {}}], thread_id="th", tags=[]
    )
    assert result == {"ok": True}


def test_agent_workflow_runs_activity(monkeypatch):
    async_mock = AsyncMock(return_value={"res": 1})
    monkeypatch.setattr(wf.workflow, "execute_activity", async_mock)
    inp = wf.AgentWorkflowInput(prompt="p", steps=[])
    result = asyncio.run(wf.AgentWorkflow().run(inp))
    async_mock.assert_awaited_once()
    args, kwargs = async_mock.call_args
    assert args == (wf.run_steps, inp)
    assert kwargs == {"schedule_to_close_timeout": wf.timedelta(minutes=10)}
    assert result == {"res": 1}


def test_agent_workflow_activity_failure(monkeypatch):
    async_mock = AsyncMock(side_effect=RuntimeError("boom"))
    monkeypatch.setattr(wf.workflow, "execute_activity", async_mock)
    inp = wf.AgentWorkflowInput(prompt="p", steps=[])
    with pytest.raises(RuntimeError, match="boom"):
        asyncio.run(wf.AgentWorkflow().run(inp))
