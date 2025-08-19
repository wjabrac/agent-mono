"""Shell execution utility."""
from __future__ import annotations

import sys
from typing import Dict, List
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from config import POLICY_ENGINE_ENABLED
from agent_mono import policy
from agent_mono.shell_utils import run_shell


def _check_policy(capability: str) -> None:
    if not POLICY_ENGINE_ENABLED:
        return
    policy.check(capability)


def shell_run_sandboxed(argv: List[str]) -> Dict:
    """Execute a shell command with policy enforcement."""
    _check_policy("subprocess")
    return run_shell(argv)
