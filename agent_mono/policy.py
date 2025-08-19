from __future__ import annotations
import json, threading, time
from pathlib import Path
from typing import Dict, Literal

_POLICY = {"capabilities": {}}  # type: Dict[str, Dict[str, Literal["allow","deny"]]]
_LOCK = threading.RLock()
_MTIME = 0.0
_PATH = Path(__file__).resolve().parents[1] / "policies.json"

class PolicyError(RuntimeError):
    pass

def _reload_if_needed() -> None:
    global _MTIME
    try:
        mtime = _PATH.stat().st_mtime
    except FileNotFoundError:
        raise PolicyError("policies.json not found")
    if mtime <= _MTIME:
        return
    data = json.loads(_PATH.read_text(encoding="utf-8"))
    caps = data.get("capabilities", {})
    if not isinstance(caps, dict):
        raise PolicyError("invalid policy format")
    for k, v in caps.items():
        if v.get("default") not in ("allow", "deny"):
            raise PolicyError(f"invalid default for {k}")
    _POLICY.clear()
    _POLICY.update({"capabilities": caps})
    _MTIME = mtime

def check(capability: str) -> None:
    with _LOCK:
        _reload_if_needed()
        action = _POLICY["capabilities"].get(capability, {}).get("default", "allow")
        if action == "deny":
            raise PermissionError(f"{capability} denied")
