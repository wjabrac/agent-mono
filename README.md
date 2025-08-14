
## Quick start

For development conventions and testing commands, see AGENTS.md.
For an overview of outstanding work and integration plans, see docs/project-scope.md.


---

## Document 2 — `README.md`

```markdown
# Quick start

This guide shows how to try the experimental agent runtime.

## Installation

```bash
pip install --no-deps -e .


Any Python package manager can be used. The project targets Python 3.10+.

Creating a plugin
agent create plugin my_plugin


A new folder plugins/my_plugin is created with a minimal ToolSpec that you can extend.
To scaffold a service instead:

agent create service my_service

Enabling optional modules

All advanced features are disabled by default. Enable them with environment variables:

export TOOL_HOT_RELOAD=true              # reload plugins without restart
export POLICY_ENGINE_ENABLED=true        # allowlist, path restrictions, rate limits
export ADVANCED_PLANNING=true            # plan conditionals and loops
export HITL_DEFAULT=true                 # require human approvals


A hitl.ok file in the repository root approves paused waves when HITL is enabled.

For design details see docs/architecture/tool-runtime-and-planning.md.
For development guidelines, consult AGENTS.md.

Optional auxiliary tooling via Docker

Bring up auxiliary services (Redis, n8n, Node-RED, Prefect, a TensorFlow/LangChain/LlamaIndex API, Odoo, WordPress, MariaDB, and Mautic) via Docker:

docker compose -f docker/docker-compose.yml up -d


They provide orchestration, content management, and ML capabilities for experiments.

TypeScript example agent

An experimental TypeScript agent is available under services/ts-agent.

cd services/ts-agent
npm test            # type-check
npm run build       # compile
node dist/cli.js    # run the REPL

