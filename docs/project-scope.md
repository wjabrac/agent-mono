# Project scope and integration roadmap

This document outlines the remaining work to fully integrate the experimental agent runtime, tool plugins, and service suite.

## Existing components
- **CLI and scaffolding**: `agent create` generates plugin and service templates.
- **Core runtime**: modules under `core/` provide tool registry, policy engine, planning, memory, and observability.
- **Services**: example Temporal worker in `services/temporal-worker` executes workflows against the core runtime.
- **Docs**: quickstart, architecture, and tool/policy guides describe basic usage and feature flags.

## Outstanding work
1. **Documentation**
   - Add guides for developing plugins and deploying services.
   - Expand policy and configuration references for production setups.
   - Describe observability, logging, and tracing options.
2. **Tool integration**
   - Audit existing plugins for completeness and error handling.
   - Expose remote tool registration through configuration and CLI helpers.
   - Harden sandboxing for risky tools and enforce rate limits consistently.
3. **Service orchestration**
   - Flesh out the Temporal worker example into a reusable service package.
   - Document how services discover plugins and share policy settings.
   - Provide deployment examples (Docker, compose, and cloud workflows).
4. **Planning and HITL**
   - Stabilize advanced planning features and reflection checkpoints.
   - Improve human‑in‑the‑loop flows and document approval mechanisms.
5. **Testing and quality**
   - Increase unit and integration test coverage for registry, policy, and planning modules.
   - Add end‑to‑end scenarios that exercise plugin, service, and workflow interactions.

## Next steps
1. Draft plugin and service development guides.
2. Build deployment examples demonstrating tool integration across services.
3. Expand automated tests and observability to validate the full suite.

For contributor guidelines, see [AGENTS.md](../AGENTS.md). Existing usage docs remain in [README.md](../README.md) and [docs/quickstart.md](quickstart.md).
