from __future__ import annotations

import json
import sys
import threading
import time
from pathlib import Path
from typing import Any, Dict, Iterable

from . import logger
from config import POLICY_ENGINE_ENABLED, POLICY_PATH

_CAPABILITY_REGISTRY = {"fs.read", "fs.write", "network", "subprocess"}

_POLICY: Dict[str, Any] = {"capabilities": {}}
_LOCK = threading.RLock()
_MTIME = 0.0
_PATH = Path(POLICY_PATH).resolve()


class PolicyError(RuntimeError):
    pass


def _is_subpath(path: Path, prefix: Path) -> bool:
    try:
        path.relative_to(prefix)
        return True
    except ValueError:
        return False


def _validate(data: Dict[str, Any]) -> Dict[str, Any]:
    if set(data.keys()) != {"capabilities"}:
        raise PolicyError("invalid policy format")
    caps = data.get("capabilities", {})
    if set(caps.keys()) != _CAPABILITY_REGISTRY:
        missing = _CAPABILITY_REGISTRY - set(caps.keys())
        extra = set(caps.keys()) - _CAPABILITY_REGISTRY
        if missing:
            raise PolicyError(f"missing capabilities: {', '.join(sorted(missing))}")
        if extra:
            raise PolicyError(f"unknown capabilities: {', '.join(sorted(extra))}")
    new_caps: Dict[str, Dict[str, Any]] = {}
    for cap, cfg in caps.items():
        if cfg.get("default") not in {"allow", "deny"}:
            raise PolicyError(f"invalid default for {cap}")
        allowed = [Path(p).resolve() for p in cfg.get("allowed_paths", [])]
        forbidden = [Path(p).resolve() for p in cfg.get("forbidden_paths", [])]
        new_caps[cap] = {
            "default": cfg["default"],
            "allowed_paths": allowed,
            "forbidden_paths": forbidden,
        }
    return {"capabilities": new_caps}


def _reload_if_needed() -> None:
    global _MTIME
    try:
        mtime = _PATH.stat().st_mtime
    except FileNotFoundError as e:
        raise PolicyError("policies.json not found") from e
    if mtime <= _MTIME:
        return
    text = _PATH.read_text(encoding="utf-8")
    try:
        data = json.loads(text)
        new_policy = _validate(data)
    except Exception as e:
        if _MTIME == 0:
            raise PolicyError(str(e))
        logger.log_event("policy.reload_error", error=str(e))
        return
    _POLICY.clear()
    _POLICY.update(new_policy)
    _MTIME = mtime


def check(capability: str, *, path: Path | None = None, source: str = "unknown") -> None:
    if not POLICY_ENGINE_ENABLED:
        return
    with _LOCK:
        _reload_if_needed()
        caps = _POLICY["capabilities"]
        if capability not in caps:
            logger.log_event("policy.deny", capability=capability, action="deny", source=source, reason="undefined")
            raise PermissionError(f"capability undefined: {capability}")
        cfg = caps[capability]
        if path is not None:
            rp = path.expanduser().resolve()
            allowed: Iterable[Path] = cfg.get("allowed_paths", [])
            if allowed and not any(_is_subpath(rp, p) for p in allowed):
                logger.log_event(
                    "policy.deny",
                    capability=capability,
                    action="deny",
                    source=source,
                    reason="path_not_allowed",
                    path=str(rp),
                )
                raise PermissionError(f"path not allowed: {rp}")
            for fp in cfg.get("forbidden_paths", []):
                if _is_subpath(rp, fp):
                    logger.log_event(
                        "policy.deny",
                        capability=capability,
                        action="deny",
                        source=source,
                        reason="path_forbidden",
                        path=str(rp),
                    )
                    raise PermissionError(f"path forbidden: {rp}")
        action = cfg.get("default", "deny")
        if action == "deny":
            logger.log_event("policy.deny", capability=capability, action="deny", source=source)
            raise PermissionError(f"{capability} denied")
        logger.log_event("policy.allow", capability=capability, action="allow", source=source)


try:
    with _LOCK:
        _reload_if_needed()
except PolicyError as e:  # fail fast on startup
    print(f"policy error: {e}. See README for policy configuration.", file=sys.stderr)
    sys.exit(78)
