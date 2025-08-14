import sys
import asyncio
import os
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock
import pytest

SERVICE_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.append(str(SERVICE_DIR))
sys.path.append(str(REPO_ROOT))

import main


def test_main_runs(monkeypatch):
    start_mock = MagicMock()
    monkeypatch.setattr(main, "start_http_server", start_mock)

    async def fake_connect(addr):
        assert addr == "temporal:7233"
        return "client"

    monkeypatch.setattr(main.Client, "connect", fake_connect, raising=False)

    run_mock = AsyncMock()

    class DummyWorker:
        def __init__(self, client, task_queue, workflows, activities):
            assert client == "client"
            assert task_queue == "agent-tq"
            assert workflows == [main.AgentWorkflow]
            assert activities == [main.run_steps]
            self.run = run_mock

    monkeypatch.setattr(main, "Worker", DummyWorker)

    asyncio.run(main.main())

    start_mock.assert_called_once_with(9109)
    run_mock.assert_awaited_once()


def test_main_worker_failure(monkeypatch):
    start_mock = MagicMock()
    monkeypatch.setattr(main, "start_http_server", start_mock)

    async def fake_connect(addr):
        return "client"

    monkeypatch.setattr(main.Client, "connect", fake_connect, raising=False)

    run_mock = AsyncMock(side_effect=RuntimeError("fail"))

    class DummyWorker:
        def __init__(self, client, task_queue, workflows, activities):
            self.run = run_mock

    monkeypatch.setattr(main, "Worker", DummyWorker)

    with pytest.raises(RuntimeError, match="fail"):
        asyncio.run(main.main())
