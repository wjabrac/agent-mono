---
id: dev-guide-integration-n8n-crewai
title: Integrations: n8n, CrewAI, and more
sidebar_label: Integrations (n8n, CrewAI)
---

This guide shows how to integrate external automation and agent orchestrators with AutoAgent.

n8n integration (webhooks):
- Compose already includes an `n8n` service. Create a workflow with a Webhook trigger (POST) at `/webhook/autoagent-run`.
- Add an HTTP Request node to call AutoAgent:
  - Method: POST
  - URL: `http://autoagent-core:8080/run`
  - Body (JSON):
    ```json
    {
      "prompt": "Fetch https://example.com and summarize",
      "steps": null
    }
    ```
- Optionally call `/run_async` to offload to Temporal.
- Use subsequent nodes (e.g., Slack, Email, GitHub) to route results.

n8n consuming insights:
- Add an HTTP Request node to `GET http://autoagent-core:8080/insights` for operational metrics to power alerts and dashboards.

CrewAI integration:
- Use CrewAI to orchestrate multiple high-level tasks, and delegate concrete tool work to AutoAgent via HTTP.
- Example CrewAI agent step:
  ```python
  import requests
  def execute_autoagent(prompt: str, steps=None):
      r = requests.post("http://autoagent-core:8080/run", json={"prompt": prompt, "steps": steps})
      r.raise_for_status()
      return r.json()
  ```
- For long-running tasks in CrewAI, call `/run_async` and persist `workflow_id`/`run_id` in Crew state.

Webhooks from AutoAgent (optional):
- Add a microtool that posts to an n8n webhook URL, enabling event-driven bridging from within tool runs.
  - Create a file in `tools/notify.py`:
    ```python
    import requests
    from core.tools.microtool import microtool

    @microtool("notify.n8n", description="POST payload to n8n webhook")
    def notify_n8n(url: str, payload: dict):
        r = requests.post(url, json=payload, timeout=10)
        r.raise_for_status()
        return {"status": "ok"}
    ```
  - Set `MICROTOOL_DIRS=tools` and the registry will auto-load it.

Other integrators:
- Langfuse: already included via docker-compose. You can export traces by adapting `core/observability/trace.py` to emit spans to Langfuse.
- Zapier/Make: mirror the n8n pattern using their respective webhooks.

Security considerations:
- Use `core/security/policy.py` to restrict risky tools (e.g., `mcp.shell.run`). Adjust `RISKY_TOOLS` via env.
- Add auth in front of FastAPI (proxies or API keys) before exposing externally.