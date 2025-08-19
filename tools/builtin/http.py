"""HTTP fetch utility."""
from __future__ import annotations

import sys
from typing import Dict
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from config import POLICY_ENGINE_ENABLED
from agent_mono import policy
from agent_mono.http_utils import fetch_text


def _check_policy(capability: str) -> None:
    if not POLICY_ENGINE_ENABLED:
        return
    policy.check(capability)


def http_fetch_text(url: str) -> Dict:
    """Fetch text from a URL after policy check."""
    _check_policy("network")
    text = fetch_text(url)
    return {"success": True, "text": text}
