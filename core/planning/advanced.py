import os
from typing import Any, Dict, List

ADVANCED_PLANNING = os.getenv("ADVANCED_PLANNING", "false").lower() in ("1","true","yes")


def expand_plan(raw_steps: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    if not ADVANCED_PLANNING:
        return raw_steps
    expanded: List[Dict[str, Any]] = []

    def _is_truthy(val: Any) -> bool:
        if isinstance(val, bool):
            return val
        if isinstance(val, (int, float)):
            return val != 0
        if isinstance(val, str):
            return val.lower() in ("true", "1", "yes", "always")
        return bool(val)

    def _expand(seq: List[Dict[str, Any]]) -> None:
        for item in seq:
            if "if" in item and isinstance(item.get("then"), list):
                cond = item.get("if")
                truthy = _is_truthy(cond)
                _expand(item.get("then", []) if truthy else item.get("else", []))
            elif "while" in item and isinstance(item.get("steps"), list):
                spec = item.get("while") or {}
                # Evaluate initial condition once; bounded by max
                cond = _is_truthy(spec.get("cond", True))
                max_iters = int(spec.get("max", 1) or 1)
                if cond:
                    for _ in range(max(0, max_iters)):
                        _expand(item.get("steps", []))
            elif "loop" in item and isinstance(item.get("steps"), list):
                spec = item.get("loop") or {}
                n = int(spec.get("range", spec.get("times", 0)) or 0)
                for _ in range(max(0, n)):
                    _expand(item.get("steps", []))
            else:
                expanded.append(item)

    _expand(raw_steps)
    return expanded