"""Simple CLI entrypoint for the agent runtime."""
from __future__ import annotations

import argparse
import json
import os

import time


def start_execution_plan(instruction: str) -> None:
    """Load tools, plan steps, and execute the plan."""
    from core.tools import registry
    from core.agentControl import execute_steps, plan_steps
    from core.observability.trace import start_trace, log_event
    from core.trace_context import set_trace
    from . import policy

    trace_id = start_trace()
    set_trace(None, trace_id, [])

    policy.check("plugins.load")
    t0 = time.time()
    registry.discover("plugins")
    discover_ms = int((time.time() - t0) * 1000)
    try:
        log_event(trace_id, "runtime", "discover", {"ms": discover_ms, "tools": registry.names()})
    except Exception:
        pass

    policy.check("plan.generate")
    t1 = time.time()
    plan = plan_steps(instruction)
    plan_ms = int((time.time() - t1) * 1000)
    try:
        log_event(trace_id, "runtime", "plan", {"ms": plan_ms, "steps": plan})
    except Exception:
        pass
    available = set(registry.names())
    missing = [step for step in plan if step.get("tool") not in available]
    plan = [step for step in plan if step.get("tool") in available]
    if missing:
        try:
            log_event(trace_id, "runtime", "plan_filtered", {"missing": missing})
        except Exception:
            pass

    policy.check("plan.execute")
    t2 = time.time()
    result = execute_steps(instruction, steps=plan, trace_id=trace_id)
    exec_ms = int((time.time() - t2) * 1000)
    try:
        log_event(trace_id, "runtime", "execute", {"ms": exec_ms})
    except Exception:
        pass
    print(json.dumps(result, indent=2))


def run_agent(instruction: str, dry_run: bool = False) -> None:
    """Normalize the instruction and start execution."""
    normalized = instruction.strip()
    if dry_run:
        print(f"dry run: {normalized}")
        return
    start_execution_plan(normalized)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run a single instruction")
    parser.add_argument("instruction", type=str, help="Instruction for the agent")
    parser.add_argument("--policy", type=str, help="Path to policy file")
    parser.add_argument("--dry-run", action="store_true", help="Parse but do not execute")
    args = parser.parse_args()
    if args.policy:
        os.environ["POLICY_PATH"] = args.policy
    run_agent(args.instruction, dry_run=args.dry_run)
