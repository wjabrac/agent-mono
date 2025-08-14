# Quick start

Document 1 — docs/quickstart.md
# Quick start

1. **Install dependencies**

   Use any Python package manager to install the project in editable mode:

   ```bash
   pip install --no-deps -e .


Create a plugin template

agent create plugin my_plugin


This generates plugins/my_plugin with a stub ToolSpec implementation.

To scaffold a new service instead:

agent create service my_service


which creates services/my_service with a minimal FastAPI app.

Enable optional features (all disabled by default)

export TOOL_HOT_RELOAD=true              # dynamic plugin reloads
export POLICY_ENGINE_ENABLED=true        # allowlist, FS roots, rate limits
export ADVANCED_PLANNING=true            # conditionals/loops in plans
export HITL_DEFAULT=true                 # require human approvals


A hitl.ok file in the repository root approves human-in-the-loop pauses when HITL is enabled.

See docs/quickstart.md for more details.

Optional auxiliary tooling via Docker

Run supporting services like Redis, n8n, Node-RED, a Prefect scheduler, a TensorFlow/LangChain/LlamaIndex API, Odoo, WordPress, MariaDB, and Mautic with Docker Compose:

docker compose -f docker/docker-compose.yml up -d


These are optional and help integrate orchestration, content systems, and ML workflows.

TypeScript example agent

An experimental TypeScript agent lives in services/ts-agent and showcases the tool, memory, and security modules.

cd services/ts-agent
npm test            # type-check the sources
npm run build       # compile to JavaScript
node dist/cli.js    # start the REPL interface


This agent uses DuckDuckGo search, file analysis, and a vector memory backed by ChromaDB.

Tool registry, policy, HITL, and planning (experimental)

Feature-flagged modules add dynamic tool loading, a policy engine, and advanced planning:

Registry: core.tools.registry supports hot-load and remote tool configs (REMOTE_TOOLS_CONFIG).

Policy: core.security.policy provides allowlist, path restrictions (FS_SAFE_ROOTS), and HTTP rate limiting.

HITL: HITL_DEFAULT controls per-wave approvals; drop a hitl.ok file to approve.

Planning: core.planning.advanced enables conditional/loop expansion; core.planning.reflection adds checkpoints.

All are disabled by default. See docs/architecture/tool-runtime-and-planning.md.
