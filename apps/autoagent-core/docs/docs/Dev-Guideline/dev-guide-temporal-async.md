---
id: dev-guide-temporal-async
title: Async execution with Temporal
sidebar_label: Temporal Async
---

This runtime supports asynchronous execution via Temporal.

How it works:
- The API (`/run_async`) connects to `TEMPORAL_HOST` and starts the workflow named `AgentWorkflow` with arguments `(prompt, steps, thread, tags)`.
- The Temporal worker listens on task queue `agent-tq` and runs the `run_steps` activity, which calls the same `execute_steps` as the sync path.

Run locally with docker-compose:
- `docker/docker-compose.yml` includes a `temporal` service, the `autoagent-core` API, and a `temporal-worker` service.
- Start all services:
  ```bash
  docker compose -f docker/docker-compose.yml up --build
  ```
- Call the async API:
  ```bash
  curl -s http://localhost:8080/run_async -H 'content-type: application/json' \
    -d '{"prompt":"test async", "steps": null}'
  ```

Notes:
- The app starts workflows by name; no import coupling to the worker module.
- Tune timeouts and retries in `services/temporal-worker/workflow.py` and tool specs.
- Set `TEMPORAL_HOST` to point to your Temporal cluster.