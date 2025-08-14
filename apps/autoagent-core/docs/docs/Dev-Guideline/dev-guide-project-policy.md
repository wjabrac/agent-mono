---
id: dev-guide-project-policy
title: Project Policy (Local-only, No Paid Services)
sidebar_label: Project Policy
---

This project is intended for local, backyard use only. To keep costs at zero:

- Do not add Prometheus, exporters, or any Prometheus dependencies.
- Do not add paid SaaS services or cloud-only vendors.
- Prefer local-only, open-source components already in compose (Temporal, n8n, Qdrant, Meilisearch, Langfuse, Ollama). All are optional.
- Observability must use the built-in counters and the `/insights` endpoint.
- If you need dashboards, build lightweight local pages or use n8n flows to poll `/insights` and render—no external services.
- Disable or remove any optional containers you don’t need to reduce resource usage.

Accepted patterns:
- `GET /insights` for a one-stop operational snapshot (success rates, p50/p95 latency, skip/error rollups).
- Persisting insights to a local JSON file and viewing it with a simple static page or CLI.
- n8n webhook-driven flows to notify you locally (e.g., desktop notifications) without any third-party SaaS.

Non-negotiable rule:
- No Prometheus. No paid telemetry. Keep it local and free.