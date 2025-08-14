
## Tool registry, policy, HITL, and planning (experimental)

Feature-flagged modules add dynamic tool loading, a policy engine, and advanced planning:

- Registry: `core.tools.registry` supports hot-load and remote tool configs (`REMOTE_TOOLS_CONFIG`).
- Policy: `core.security.policy` provides allowlist, path restrictions (`FS_SAFE_ROOTS`), and HTTP rate limiting.
- HITL: `HITL_DEFAULT` controls per-wave approvals; drop a `hitl.ok` file to approve.
- Planning: `core.planning.advanced` enables conditional/loop expansion; `core.planning.reflection` adds checkpoints.

All are disabled by default. See `docs/architecture/tool-runtime-and-planning.md`.