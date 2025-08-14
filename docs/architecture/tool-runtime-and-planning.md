# Tool runtime hardening and agent planning upgrades

This document outlines the design for the hardened tool runtime and upgraded planning.

## Feature flags
- `TOOL_HOT_RELOAD=false`: enable hot reload and remote tool config watching.
- `REMOTE_TOOLS_CONFIG=`: JSON file describing remote tools.
- `POLICY_ENGINE_ENABLED=false`: enable policy checks and rate limits.
- `FS_SAFE_ROOTS=`: comma-separated safe directories for FS paths.
- `ALLOWED_TOOLS=`: allowlist of tool names.
- `HTTP_RATE_LIMIT_PER_MIN=0`: per-minute HTTP rate limit.
- `RISKY_TOOLS=mcp.shell.run`: executed via sandbox.
- `ADVANCED_PLANNING=false`: enable conditional/loop expansion for plans.
- `ENABLE_REFLECTION=false`: enable self-reflection checkpoints.
- `HITL_DEFAULT=true`: require approval on multi-phase waves.

## Tool extensibility
- Dynamic `core.tools.registry` loads `plugins/*` ToolSpec objects and can hot-reload.
- Optional remote tools loaded from a JSON file via `core.tools.remote` adapter with per-tool API keys.

## Error handling and resilience
- Centralized execution wrapper in `core.agentControl._run_with_policy` adds retries, timeouts, caching, and logs to traces. Structured metrics are emitted.

## Planning
- `core.planning.advanced.expand_plan` expands conditional and loop constructs into flat steps for DAG execution.
- Parallel DAG waves execute with dependency awareness.
- `core.planning.reflection.maybe_replan` adds checkpoints that can trigger additional steps.

## Security and policy
- `core.security.policy` enforces allowlist, path restrictions, and HTTP rate limits.
- Risky tools are executed in a separate process via `core.security.sandbox`.

## Human-in-the-loop
- Existing approval mechanism waits for a token file. With flags, phases pause before multi-step waves.

## Knowledge integration
- Persisted traces and tool cache stored in SQLite (`core.memory.db`). Future work: index traces in a vector DB.

## Multimodal IO
- New `plugins`: `csv_parse`, `json_parse`, and `image_info` for CSV, JSON, image metadata.

## Agent collaboration
- Minimal hooks: multiple steps and dependencies support delegation patterns. Future work: specialized agent classes.

## Testing
- Unit tests cover registry hot-load, policy checks, retries, and planning conditionals. A smoke e2e test validates `execute_steps`.