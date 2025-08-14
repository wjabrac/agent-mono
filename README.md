# Quick start

This guide shows how to try the experimental agent runtime.

## Installation

Use any Python package manager to install the project in editable mode (Python 3.10+):

```bash
pip install --no-deps -e .

Creating a plugin or service

To scaffold a new plugin:

agent create plugin my_plugin


This generates plugins/my_plugin with a minimal ToolSpec implementation.

To scaffold a new service instead:

agent create service my_service


This creates services/my_service with a minimal FastAPI app.

Enabling optional features

All advanced features are disabled by default. Enable them with environment variables:

export TOOL_HOT_RELOAD=true              # reload plugins without restart
export POLICY_ENGINE_ENABLED=true        # allowlist, FS roots, rate limits
export ADVANCED_PLANNING=true            # conditionals and loops in plans
export HITL_DEFAULT=true                 # require human approvals


A hitl.ok file in the repository root approves paused waves when HITL is enabled.

For design details see docs/architecture/tool-runtime-and-planning.md.
For development guidelines, consult AGENTS.md.

Optional auxiliary tooling via Docker

Run supporting services like Redis, n8n, Node-RED, Prefect scheduler, a TensorFlow/LangChain/LlamaIndex API, Odoo, WordPress, MariaDB, and Mautic with Docker Compose:

docker compose -f docker/docker-compose.yml up -d


These services are optional and provide orchestration, content management, and ML workflow capabilities.

TypeScript example agent

An experimental TypeScript agent lives in services/ts-agent and showcases the tool, memory, and security modules.

cd services/ts-agent
npm test            # type-check the sources
npm run build       # compile to JavaScript
node dist/cli.js    # start the REPL interface


This agent uses DuckDuckGo search, file analysis, and a vector memory backed by ChromaDB.

Tool registry, policy, HITL, and planning (experimental)

Feature-flagged modules add dynamic tool loading, a policy engine, and advanced planning:

Registry: core.tools.registry supports hot-load and remote tool configs via REMOTE_TOOLS_CONFIG.

Policy: core.security.policy provides allowlist, path restrictions (FS_SAFE_ROOTS), and HTTP rate limiting.

HITL: HITL_DEFAULT controls per-wave approvals; drop a hitl.ok file to approve.

Planning: core.planning.advanced enables conditional/loop expansion; core.planning.reflection adds checkpoints.

All are disabled by default. See docs/architecture/tool-runtime-and-planning.md.

For development conventions and testing commands, see AGENTS.md.
For an overview of outstanding work and integration plans, see docs/project-scope.md.


If you drop that into your **`README.md`**, it will fully cover both quick start instructions and the extra sections from `docs/quickstart.md`.  

Do you also want me to **include a troubleshooting block** in this merged README for the `"agent: command not found"` issue you’re having so new installs don’t hit the same problem? That way you won’t have to remember the fix later.
