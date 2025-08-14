# Quick start

This guide shows how to try the experimental agent runtime.

## Installation

```bash
pip install -e .
```

Any Python package manager can be used. The project targets Python 3.10+.

## Creating a plugin

```bash
python tools/agent_plugin_cli.py plugin create my_plugin
```

A new folder `plugins/my_plugin` is created with a minimal `ToolSpec` that you
can extend.

## Enabling optional modules

All advanced features are disabled by default. Enable them with environment variables:

```bash
export TOOL_HOT_RELOAD=true              # reload plugins without restart
export POLICY_ENGINE_ENABLED=true        # allowlist, path restrictions, rate limits
export ADVANCED_PLANNING=true            # plan conditionals and loops
export HITL_DEFAULT=true                 # require human approvals
```

A `hitl.ok` file in the repository root approves paused waves when HITL is enabled.

For design details see [`docs/architecture/tool-runtime-and-planning.md`](architecture/tool-runtime-and-planning.md).

