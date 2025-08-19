"""Simple CLI entrypoint for the agent runtime."""
from __future__ import annotations

import argparse


def start_execution_plan(instruction: str) -> None:
    """Internal stub for starting an execution plan."""
    print(instruction)


def run_agent(instruction: str) -> None:
    """Normalize the instruction and start execution."""
    normalized = instruction.strip()
    start_execution_plan(normalized)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run a single instruction")
    parser.add_argument("instruction", type=str, help="Instruction for the agent")
    args = parser.parse_args()
    run_agent(args.instruction)
