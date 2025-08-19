"""Filesystem write utility."""
from __future__ import annotations

import sys
import difflib
from pathlib import Path
from typing import Dict

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from config import POLICY_ENGINE_ENABLED
from agent_mono import policy
from agent_mono.fs_utils import write_text_atomic


def _check_policy(capability: str) -> None:
    if not POLICY_ENGINE_ENABLED:
        return
    policy.check(capability)


def fs_write_text(path: Path, content: str) -> Dict:
    """Write text to a file after policy check."""
    _check_policy("fs.write")
    original = path.read_text() if path.exists() else ""
    write_text_atomic(path, content)
    diff = "\n".join(
        difflib.unified_diff(original.splitlines(), content.splitlines(), lineterm="")
    )
    return {"success": True, "diff": diff}
