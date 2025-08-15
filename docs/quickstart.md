# Quick start

This guide shows how to try the experimental agent runtime.

## Installation

```bash
pip install --no-deps -e .
```

Any Python package manager can be used. The project targets Python 3.10+.

## Creating a plugin

```bash
agent create plugin my_plugin
```

A new folder `plugins/my_plugin` is created with a minimal `ToolSpec` that you
can extend. To scaffold a service instead:

```bash
agent create service my_service
```

## Enabling optional modules

All advanced features are disabled by default. Enable them with environment variables:

```bash
export TOOL_HOT_RELOAD=true              # reload plugins without restart
export POLICY_ENGINE_ENABLED=true        # allowlist, path restrictions, rate limits
export ADVANCED_PLANNING=true            # plan conditionals and loops
export HITL_DEFAULT=true                 # require human approvals
```

For design details see [`docs/architecture/tool-runtime-and-planning.md`](architecture/tool-runtime-and-planning.md).

## TypeScript agent

Install dependencies and start the Node-based agent:

```bash
npm install
npm start
```

For development guidelines, consult [AGENTS.md](../AGENTS.md).

## Metrics stack

Generate a `.env` with strong credentials (run `./docker/gen-env.sh` or copy `.env.example` and edit), then start Graphite and Grafana with the `metrics` profile:

```bash
./docker/gen-env.sh               # generate .env with random secrets
# or
cp .env.example .env              # edit values manually
docker compose -f docker/docker-compose.yml --profile metrics up
```

Grafana listens on port 3001 and Graphite's web UI on port 8083. Both require the
credentials supplied in `.env` and Grafana includes a sample alert rule. Postgres (5432) and MariaDB (3306) are bound to 127.0.0.1 for local access only. For production, place a TLS-terminating proxy with authentication in front of all HTTP services.

