# Agent Mono

Unified runtime for Python and TypeScript agents. The repo includes:
- Python CLI entry point for tools, planning, and execution
- TypeScript agent runtime with planning, response generation, and security utilities
- Plugin system for tools, with hot reload and policy controls

## Install

Python
```bash
python -m venv .venv && source .venv/bin/activate  # use Scripts\activate on Windows
pip install --no-deps -e .
