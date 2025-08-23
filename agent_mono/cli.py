"""Simple CLI entrypoint for the agent runtime."""
from __future__ import annotations

import argparse
import json
import os
import sys
import time

# Keep OTEL off by default; enable via env for tracing.
os.environ.setdefault("OTEL_SDK_DISABLED", "true")

from core.tools import registry
from core.agentControl import execute_steps, plan_steps
from core.observability.trace import start_trace
from agent_mono import policy
from plugins.sandbox import SandboxTimeout  # exit-code mapping

EXIT_OK = 0
EXIT_ERROR = 1
EXIT_POLICY_DENIED = 2
EXIT_SANDBOX_ERROR = 3
EXIT_MISSING_TOOL = 4


def run_agent(
    instruction: str, *, dry_run: bool = False, policy_path: str | None = None
) -> int:
    """One-shot: normalize → discover → plan → execute with policy checks.

    Contract: exactly one JSON to stdout; diagnostics to stderr; fixed exit codes.
    """
    normalized = instruction.strip()

    policy.load(policy_path)
    snap = policy.snapshot()
    print(
        f"policy mode={snap['mode']} path={snap.get('path','<default>')} schema={snap['version']}",
        file=sys.stderr,
    )

    if dry_run:
        print(json.dumps({"instruction": normalized, "tools": [], "version": snap["version"], "dry_run": True}))
        return EXIT_OK

    trace_id = start_trace()
    try:
        # Discover once (entry points only)
        policy.check("plugins.load")
        t0 = time.time()
        registry.discover()
        names = sorted(registry.names())
        print(f"discovered {len(names)} tools in {int((time.time()-t0)*1000)} ms: {', '.join(names)}", file=sys.stderr)

        # Plan once
        policy.check("plan.generate")
        t1 = time.time()
        plan = plan_steps(normalized)
        print(f"plan.generate {int((time.time()-t1)*1000)} ms", file=sys.stderr)

        # Integrity: the plan that executes is the plan produced
        available = set(names)
        missing = [s for s in plan if s.get("tool") not in available]
        if missing:
            missing_names = sorted({s.get("tool") for s in missing if s.get("tool")})
            msg = f"missing tools: {', '.join(missing_names)}"
            print(msg, file=sys.stderr)
            print(json.dumps({"instruction": normalized, "version": snap["version"], "error": msg}))
            return EXIT_MISSING_TOOL

        # Execute once
        policy.check("plan.execute")
        t2 = time.time()
        result = execute_steps(normalized, steps=plan, trace_id=trace_id)
        print(f"plan.execute {int((time.time()-t2)*1000)} ms", file=sys.stderr)

        print(json.dumps(result))
        return EXIT_OK

    except PermissionError as e:
        print(str(e), file=sys.stderr)
        print(json.dumps({"instruction": normalized, "version": snap["version"], "error": str(e)}))
        return EXIT_POLICY_DENIED
    except (SandboxTimeout, RuntimeError) as e:
        print(str(e), file=sys.stderr)
        print(json.dumps({"instruction": normalized, "version": snap["version"], "error": str(e)}))
        return EXIT_SANDBOX_ERROR
    except Exception as e:
        print(str(e), file=sys.stderr)
        print(json.dumps({"instruction": normalized, "version": snap["version"], "error": str(e)}))
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
