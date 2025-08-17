# Agent runtime

This project provides a modular runtime for building and testing agentic workflows.

## Architecture

```mermaid
graph TD
    User --> AgentCLI
    AgentCLI --> PluginManager
    PluginManager --> Services
    Services --> ExternalAPIs
```

## Features

- Scaffold plugins and services with the `agent` CLI.
- Hot-reload tools during development.
- Policy engine for security controls.
- Advanced planning with loops and conditionals.
- Human-in-the-loop approvals.
- Metrics and tracing via Graphite and Grafana.

## Basic usage

### Installation

```bash
pip install --no-deps -e .
```

### Create a plugin

```bash
agent create plugin my_plugin
```

### Enable optional modules

```bash
export ADVANCED_PLANNING=true
export POLICY_ENGINE_ENABLED=true
```

See [docs/quickstart.md](docs/quickstart.md) for more examples.

## Metrics stack

Graphite and Grafana services are included in `docker/docker-compose.yml` but are
disabled by default. Start by generating a `.env` with strong credentials (run `./docker/gen-env.sh` or copy `.env.example` and
edit). Then start the monitoring stack with the `metrics` profile:

```bash
./docker/gen-env.sh               # generate .env with random secrets
# or
cp .env.example .env              # edit values manually
docker compose --profile metrics up
```

Grafana is available at [http://localhost:3001](http://localhost:3001) and the
Graphite web UI is bound to [http://localhost:8083](http://localhost:8083).
Both services authenticate using the credentials supplied in the `.env` file
and include a sample alert rule. Postgres (5432) and MariaDB (3306) are bound to 127.0.0.1 for local access only. For production
deploys, put a TLS-terminating proxy with authentication in front of all HTTP services.

