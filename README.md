
## Quick start

1. **Install dependencies**

   Use any Python package manager to install the project in editable mode:

   ```bash
   pip install --no-deps -e .
   ```

2. **Create a plugin template**

   ```bash
   agent create plugin my_plugin
   ```

   This generates `plugins/my_plugin` with a stub `ToolSpec` implementation.

   To scaffold a new service instead:

   ```bash
   agent create service my_service
   ```

   which creates `services/my_service` with a minimal FastAPI app.

3. **Enable optional features** (all disabled by default)

   ```bash
   export TOOL_HOT_RELOAD=true              # dynamic plugin reloads
   export POLICY_ENGINE_ENABLED=true        # allowlist, FS roots, rate limits
   export ADVANCED_PLANNING=true            # conditionals/loops in plans
   ```

   A `hitl.ok` file approves human-in-the-loop pauses when `HITL_DEFAULT=true`.

See [`docs/quickstart.md`](docs/quickstart.md) for more details.

## TypeScript example agent

An experimental TypeScript agent lives in `services/ts-agent` and showcases the
tool, memory, and security modules.

```bash
cd services/ts-agent
npm test            # type-check the sources
npm run build       # compile to JavaScript
node dist/cli.js    # start the REPL interface
```

This agent uses DuckDuckGo search, file analysis, and a vector memory backed by
ChromaDB.

## Tool registry, policy, HITL, and planning (experimental)

Feature-flagged modules add dynamic tool loading, a policy engine, and advanced planning:

- Registry: `core.tools.registry` supports hot-load and remote tool configs (`REMOTE_TOOLS_CONFIG`).
- Policy: `core.security.policy` provides allowlist, path restrictions (`FS_SAFE_ROOTS`), and HTTP rate limiting.
- HITL: `HITL_DEFAULT` controls per-wave approvals; drop a `hitl.ok` file to approve.
- Planning: `core.planning.advanced` enables conditional/loop expansion; `core.planning.reflection` adds checkpoints.

All are disabled by default. See `docs/architecture/tool-runtime-and-planning.md`.

---

For development conventions and testing commands, see [AGENTS.md](AGENTS.md).

For an overview of outstanding work and integration plans, see [docs/project-scope.md](docs/project-scope.md).
