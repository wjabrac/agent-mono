# Quick start

This guide shows how to try the experimental agent runtime. For an overview of the architecture and features, see the [README](../README.md).

## Installation

```bash
pip install --no-deps -e .
```

Any Python package manager can be used. The project targets Python 3.10+.

## Running an instruction

```bash
python -m agent_mono.cli --dry-run "list files in /tmp"
```

## Creating a plugin

```bash
agent create plugin my_plugin
```

A new folder `plugins/my_plugin` is created with a minimal `ToolSpec` that you
can extend. To scaffold a service instead:

```bash
agent create service my_service
```

## Advanced modules

Planning and human approvals are experimental and not yet implemented. The
policy engine is enabled by default; see the [README](../README.md) for the
security model and configuration.

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
docker compose --profile metrics up
```

Grafana listens on port 3001 and Graphite's web UI on port 8083. Both require the
credentials supplied in `.env` and Grafana includes a sample alert rule. Postgres (5432) and MariaDB (3306) are bound to 127.0.0.1 for local access only. For production, place a TLS-terminating proxy with authentication in front of all HTTP services.


