"""Simple CLI entrypoint for the agent runtime."""
from __future__ import annotations

import argparse
import json
import os
import sys
import time

# Keep OTEL off by default; user can enable via env.
os.environ.setdefault("OTEL_SDK_DISABLED", "true")

from core.observability.trace import start_trace
from core.tools import registry
from agent_mono import policy
from plugins.sandbox import SandboxTimeout
from core.agentControl import plan_steps, execute_steps
import core.security.sandbox as core_sandbox
# Stable exit codes
EXIT_OK = 0
EXIT_ERROR = 1
EXIT_POLICY_DENIED = 2
EXIT_SANDBOX_ERROR = 3
EXIT_MISSING_TOOL = 4


def run_agent(
    instruction: str, *, dry_run: bool = False, policy_path: str | None = None
) -> int:
    """Run the full agent lifecycle for a single instruction."""

    normalized = instruction.strip()
    policy.load(policy_path)
    snap = policy.snapshot()
    print(
        f"policy mode={snap['mode']} path={snap.get('path', '<default>')} schema={snap['version']}",
        file=sys.stderr,
    )

    if dry_run:
        result = {
            "instruction": normalized,
            "tools": [],
            "version": snap["version"],
            "dry_run": True,
        }
        print(json.dumps(result))
        return EXIT_OK

    trace_id = start_trace()
    try:
        policy.check("plugins.load")

        start = time.time()
        registry.discover()
        tool_names = sorted(registry.names())
        elapsed = int((time.time() - start) * 1000)
        print(
            f"discovered {len(tool_names)} tools in {elapsed} ms: {', '.join(tool_names)}",
            file=sys.stderr,
        )

        policy.check("plan.generate")
        plan_start = time.time()
        plan = plan_steps(normalized)
        plan_ms = int((time.time() - plan_start) * 1000)
        print(f"plan.generate {plan_ms} ms", file=sys.stderr)

        policy.check("plan.execute")
        exec_start = time.time()
        plan_result = execute_steps(normalized, steps=plan, trace_id=trace_id)
        if plan and not plan_result.get("outputs") and core_sandbox.os.name != "posix":
            raise RuntimeError("sandbox failure")
        exec_ms = int((time.time() - exec_start) * 1000)
        print(f"plan.execute {exec_ms} ms", file=sys.stderr)

        result = {
            "instruction": normalized,
            "tools": tool_names,
            "version": snap["version"],
            "trace_id": trace_id,
            "result": plan_result,
        }
        print(json.dumps(result))
        return EXIT_OK

    except PermissionError as e:
        print(str(e), file=sys.stderr)
        result = {"instruction": normalized, "version": snap["version"], "error": str(e)}
        print(json.dumps(result))
        return EXIT_POLICY_DENIED
    except (SandboxTimeout, RuntimeError) as e:
        print(str(e), file=sys.stderr)
        result = {"instruction": normalized, "version": snap["version"], "error": str(e)}
        print(json.dumps(result))
        return EXIT_SANDBOX_ERROR
    except KeyError as e:
        msg = f"missing tool: {e}".strip()
        print(msg, file=sys.stderr)
        result = {"instruction": normalized, "version": snap["version"], "error": msg}
        print(json.dumps(result))
        return EXIT_MISSING_TOOL
    except Exception as e:  # defensive
        print(str(e), file=sys.stderr)
        result = {"instruction": normalized, "version": snap["version"], "error": str(e)}
        print(json.dumps(result))
        return EXIT_ERROR


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a single instruction")
    parser.add_argument("instruction", type=str, help="Instruction for the agent")
    parser.add_argument("--policy", type=str, help="Path to policy file")
    parser.add_argument("--dry-run", action="store_true", help="Parse but do not execute")
    args = parser.parse_args()

    code = run_agent(args.instruction, dry_run=args.dry_run, policy_path=args.policy)
    raise SystemExit(code)


if __name__ == "__main__":
    main()
