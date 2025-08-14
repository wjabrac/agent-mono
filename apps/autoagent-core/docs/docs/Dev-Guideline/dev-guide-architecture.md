---
id: dev-guide-architecture
title: Architecture Overview
sidebar_label: Architecture
---

This page outlines the core architecture of AutoAgent runtime used in this repo setup.

- Core runtime modules live under `core/`:
  - `core/agentControl.py`: planning and step execution with retries, timeouts, caching, fallbacks, DAG scheduling, and optional HITL checkpoints.
  - `core/tools/registry.py`: dynamic discovery and registration of tools from `plugins/` and microtools from `tools/` directories. Supports remote tool config.
  - `core/instrumentation.py`: wraps tool calls with trace events.
  - `core/observability`: lightweight counters and histograms (`metrics.py`), persisted traces in SQLite (`trace.py`), and roll-up insights (`insights.py`).
  - `core/memory/db.py`: SQLite schema and cache helpers.
  - `core/tools/microtool.py`: decorator to turn plain functions into tools.
  - `core/tools/mcp_adapter.py`: example MCP-style tools registered into the same registry.

- App and API:
  - `apps/autoagent-core/app/main.py` exposes FastAPI endpoints: `/plan`, `/run`, `/run_async`, `/tools`, `/insights`.
  - `/run` executes synchronously inside the app.
  - `/run_async` starts a Temporal workflow named `AgentWorkflow` when Temporal is available.

- Async worker:
  - `services/temporal-worker` hosts `workflow.py` and `main.py`.
  - `workflow.py` defines `AgentWorkflow` and an activity `run_steps` that calls `execute_steps` in `core/agentControl.py`.
  - `main.py` runs a Temporal worker that listens on `agent-tq`.

- Plugins:
  - Example tools live under `plugins/` such as `web_fetch.py` and `pdf_text.py`.
  - Tools are registered at import time via `ToolSpec` objects.

- Data paths:
  - SQLite DB: `AGENT_DB` env, default `data/agent_memory.sqlite`.
  - Tool manifest: `TOOLS_MANIFEST_PATH`, default `data/tools_manifest.json`.

Sequence (sync):
1. Client calls `/run` with prompt and optional steps.
2. If steps absent, the planner generates steps (local Ollama if configured, else heuristics).
3. Steps are topologically sorted and executed with retries/timeouts; metrics and traces recorded.
4. Optional reflection pass may add steps.

Sequence (async):
1. Client calls `/run_async`.
2. FastAPI starts `AgentWorkflow` by name with args (prompt, steps, thread, tags).
3. Temporal worker executes `run_steps` activity which calls the same `execute_steps`.

Environment variables of note:
- `TEMPORAL_HOST`, `HITL_DEFAULT`, `HITL_TOKEN`, `LOCAL_ROOT`, `OLLAMA_HOST`, `OLLAMA_MODEL`, `ENABLE_MCP`, `MICROTOOL_DIRS`, `REMOTE_TOOLS_CONFIG`, `RISKY_TOOLS`.