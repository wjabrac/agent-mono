"""Simple CLI entrypoint for the agent runtime."""
from __future__ import annotations

import argparse
import json
import os
import sys
import time

# Keep OTEL off by default; user can enable via env.
os.environ.setdefault("OTEL_SDK_DISABLED", "true")

from core.tools import registry
from core.agentControl import execute_steps, plan_steps
from core.observability.trace import start_trace
from agent_mono import policy
from plugins.sandbox import SandboxTimeout  # for exit-code mapping


# Stable exit codes
EXIT_OK = 0
EXIT_ERROR = 1
EXIT_POLICY_DENIED = 2
EXIT_SANDBOX_ERROR = 3
EXIT_MISSING_TOOL = 4


def run_agent(
    instruction: str, *, dry_run: bool = False, policy_path: str | None = None
) -> int:
    """Run the full agent lifecycle for a single instruction.

    Contract:
      - Exactly one discovery, one plan, one execute (unless denied/errored earlier)
      - One JSON object to stdout (single line). All diagnostics to stderr.
      - Exit codes: 0 ok, 2 policy denied, 3 sandbox error, 4 missing tool, 1 other error.
    """
    normalized = instruction.strip()

    # Load policy with CLI precedence > env > repo default.
    policy.load(policy_path)
    snap = policy.snapshot()
    print(
        f"policy mode={snap['mode']} path={snap.get('path', '<default>')} "
        f"schema={snap['version']}",
        file=sys.stderr,
    )

    if dry_run:
        result = {
            "instruction": normalized,
            "tools": [],
            "version": snap["version"],
            "dry_run": True,
        }
        print(json.dumps(result, separators=(",", ":")))
        return EXIT_OK

    trace_id = start_trace()
    try:
        # Discovery (once)
        policy.check("plugins.load")
        t0 = time.time()
        registry.discover()
        names = sorted(registry.names())
        discover_ms = int((time.time() - t0) * 1000)
        print(
            f"discovered {len(names)} tools in {discover_ms} ms: {', '.join(names)}",
            file=sys.stderr,
        )

        # Plan (once)
        policy.check("plan.generate")
        t1 = time.time()
        plan = plan_steps(normalized)
        plan_ms = int((time.time() - t1) * 1000)
        print(f"plan.generate {plan_ms} ms", file=sys.stderr)

        # Integrity: the plan that executes is the plan that was produced.
        available = set(names)
        missing = [s for s in plan if s.get("tool") not in available]
        if missing:
            missing_names = sorted(
                {s.get("tool") for s in missing if s.get("tool")}
            )
            msg = f"missing tools: {', '.join(missing_names)}"
            print(msg, file=sys.stderr)
            out = {
                "instruction": normalized,
                "version": snap["version"],
                "error": msg,
            }
            print(json.dumps(out, separators=(",", ":")))
            return EXIT_MISSING_TOOL

        # Execute (once)
        policy.check("plan.execute")
        t2 = time.time()
        result = execute_steps(
            normalized,
            steps=plan,
            trace_id=trace_id,
        )
        exec_ms = int((time.time() - t2) * 1000)
        print(f"plan.execute {exec_ms} ms", file=sys.stderr)

        # Single JSON to stdout; no extra prints.
        print(json.dumps(result, separators=(",", ":")))
        return EXIT_OK

    except PermissionError as e:
        # Policy denied.
        print(str(e), file=sys.stderr)
        out = {
            "instruction": normalized,
            "version": snap["version"],
            "error": str(e),
        }
        print(json.dumps(out, separators=(",", ":")))
        return EXIT_POLICY_DENIED

    except (SandboxTimeout, RuntimeError) as e:
        # Map sandbox/isolation errors.
        print(str(e), file=sys.stderr)
        out = {
            "instruction": normalized,
            "version": snap["version"],
            "error": str(e),
        }
        print(json.dumps(out, separators=(",", ":")))
        return EXIT_SANDBOX_ERROR

    except Exception as e:  # defensive
        print(str(e), file=sys.stderr)
        out = {
            "instruction": normalized,
            "version": snap["version"],
            "error": str(e),
        }
        print(json.dumps(out, separators=(",", ":")))
        return EXIT_ERROR


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a single instruction")
    parser.add_argument("instruction", type=str, help="Instruction for the agent")
    parser.add_argument("--policy", type=str, help="Path to policy file")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Parse but do not execute",
    )
    args = parser.parse_args()
    code = run_agent(
        args.instruction,
        dry_run=args.dry_run,
        policy_path=args.policy,
    )
    raise SystemExit(code)


if __name__ == "__main__":
    main()
