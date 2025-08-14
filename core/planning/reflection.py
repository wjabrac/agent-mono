import os
from typing import Any, Dict, List
from core.observability.trace import log_event

ENABLE_REFLECTION = os.getenv("ENABLE_REFLECTION", "false").lower() in ("1","true","yes")
REPLAN_ON_EMPTY = os.getenv("REPLAN_ON_EMPTY", "false").lower() in ("1","true","yes")


def maybe_replan(trace_id: str, prompt: str, outputs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    if not ENABLE_REFLECTION:
        return []
    log_event(trace_id, "decision", "reflect:checkpoint", {"num_outputs": len(outputs)})
    if REPLAN_ON_EMPTY and not outputs:
        log_event(trace_id, "decision", "reflect:replan", {"reason": "empty_outputs"})
        # return an empty list to force upstream planner to re-run
        return [
            {"tool": "web_fetch", "args": {"url": "https://example.com"}},
        ]
    return []