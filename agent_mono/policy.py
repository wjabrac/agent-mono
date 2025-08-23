"""Simple policy loader and checker."""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Dict, Optional

SCHEMA_VERSION = 1

CAPABILITY_REGISTRY = {
    "fs.read",
    "fs.write",
    "network",
    "subprocess",
    "plugins.load",
    "plan.generate",
    "plan.execute",
}

_POLICY: Dict[str, Dict[str, Dict[str, str]]] = {"capabilities": {}}
_PATH: Optional[Path] = None
_MODE: str = "default-deny"


def load(path: str | None = None) -> None:
    """Load policy data respecting CLI, env, and default paths."""
    global _PATH, _POLICY, _MODE
    repo_default = Path(__file__).resolve().parents[1] / "policies.json"

    def _read(p: Path) -> bool:
        global _POLICY, _MODE, _PATH
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            _POLICY = {"version": SCHEMA_VERSION, "capabilities": {}}
            _MODE = "default-deny"
            _PATH = None
            return False
        caps = data.get("capabilities", {})
        _POLICY = {"version": data.get("version", SCHEMA_VERSION), "capabilities": caps}
        _MODE = "loaded"
        _PATH = p
        return True

    if path is not None:
        _read(Path(str(path)))
        return

    env_path = os.getenv("POLICY_PATH")
    if env_path and _read(Path(env_path)):
        return
    if _read(repo_default):
        return

    _POLICY = {"version": SCHEMA_VERSION, "capabilities": {}}
    _PATH = None
    _MODE = "default-deny"


def allow(capability: str) -> bool:
    """Return True if capability is permitted."""
    return _POLICY["capabilities"].get(capability, {}).get("default", "deny") == "allow"


def check(capability: str) -> None:
    """Raise if capability is denied."""
    rule = _POLICY["capabilities"].get(capability, {})
    default = rule.get("default", "deny")
    if default != "allow":
        path = _PATH or "default-deny"
        raise PermissionError(f"{capability} denied by {path} (rule: default={default})")


def snapshot() -> Dict[str, Dict[str, Dict[str, str]]]:
    """Return a copy of current policy for debugging."""
    snap = {
        "version": _POLICY.get("version", SCHEMA_VERSION),
        "capabilities": dict(_POLICY["capabilities"]),
        "mode": _MODE,
    }
    if _PATH is not None:
        snap["path"] = str(_PATH)
    return snap
