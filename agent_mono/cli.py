"""Simple CLI entrypoint for the agent runtime."""
from __future__ import annotations

import argparse
import os


def start_execution_plan(instruction: str) -> None:
    """Internal stub for starting an execution plan."""
    print(instruction)


def run_agent(instruction: str, *, dry_run: bool = False) -> None:
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
