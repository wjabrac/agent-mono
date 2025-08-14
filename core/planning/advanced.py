import os
from typing import Any, Dict, List

ADVANCED_PLANNING = os.getenv("ADVANCED_PLANNING", "false").lower() in ("1","true","yes")


def expand_plan(raw_steps: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    if not ADVANCED_PLANNING:
        return raw_steps
    expanded: List[Dict[str, Any]] = []

    def _expand(seq: List[Dict[str, Any]]) -> None:
        for item in seq:
            if "if" in item and isinstance(item.get("then"), list):
                cond = item.get("if")
                # minimal evaluation: treat truthy strings "true/1" as True; numbers >0 as True
                truthy = False
                if isinstance(cond, bool):
                    truthy = cond
                elif isinstance(cond, str):
                    truthy = cond.lower() in ("true", "1", "yes", "always")
                elif isinstance(cond, (int, float)):
                    truthy = cond != 0
                _expand(item.get("then", []) if truthy else item.get("else", []))
            elif "loop" in item and isinstance(item.get("steps"), list):
                spec = item.get("loop") or {}
                n = int(spec.get("range", spec.get("times", 0)) or 0)
                for _ in range(max(0, n)):
                    _expand(item.get("steps", []))
            else:
                expanded.append(item)

    _expand(raw_steps)
    return expanded