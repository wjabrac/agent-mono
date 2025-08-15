README.md

# Agent Mono

Unified runtime for Python and TypeScript agents, with a plugin system, policy controls, and optional advanced planning.

## Install dependencies

Use any Python package manager to install the project in editable mode:
```bash
pip install --no-deps -e .

Create a plugin template
agent create plugin my_plugin


Generates plugins/my_plugin with a stub ToolSpec implementation.

To scaffold a new service instead:

agent create service my_service


Creates services/my_service with a minimal FastAPI app.

Enable optional features

All disabled by default.

export TOOL_HOT_RELOAD=true              # dynamic plugin reloads
export POLICY_ENGINE_ENABLED=true        # allowlist, FS roots, rate limits
export ADVANCED_PLANNING=true            # conditionals and loops in plans
export HITL_DEFAULT=false                # enable pauses when HITL is desired


A hitl.ok file approves human-in-the-loop pauses when HITL_DEFAULT=true.

See docs/quickstart.md for details.

Auxiliary tooling via Docker

Run supporting services like Redis, n8n, Node-RED, a Prefect scheduler, TensorFlow or LangChain workers, Odoo, WordPress, MariaDB, and Mautic:

docker compose -f docker/docker-compose.yml up -d

Tool registry, policy, HITL, and planning

Feature-flagged modules add dynamic tool loading, a policy engine, and advanced planning. Keep flags off in production unless you have guardrails.


docs/quickstart.md
```markdown
# Quickstart

This guide shows both Python and TypeScript flows.

## Python

Create a virtualenv and install:
```bash
python -m venv .venv && source .venv/bin/activate
pip install --no-deps -e .


Run:

agent --help      # or: python -m core.cli --help if no console script

TypeScript

Install and start:

npm install
npm start


Optional environment:

export TOOL_HOT_RELOAD=true
export POLICY_ENGINE_ENABLED=true
export ADVANCED_PLANNING=true
export HITL_DEFAULT=false


A file named hitl.ok in the repo root approves paused waves when HITL is enabled.

Docker helpers

Optional supporting services:

docker compose -f docker/docker-compose.yml up -d