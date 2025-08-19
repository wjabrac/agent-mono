"""Filesystem read utility."""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Dict

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from config import POLICY_ENGINE_ENABLED
from agent_mono import policy


def _check_policy(capability: str) -> None:
    if not POLICY_ENGINE_ENABLED:
        return
    policy.check(capability)


def fs_read(path: Path) -> Dict:
    """Read text from a file after policy check."""
    _check_policy("fs.read")
    return {"success": True, "content": path.read_text()}
