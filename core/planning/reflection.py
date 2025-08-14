import os
from typing import Any, Dict, List
from core.observability.trace import log_event

ENABLE_REFLECTION = os.getenv("ENABLE_REFLECTION", "false").lower() in ("1","true","yes")
REPLAN_ON_EMPTY = os.getenv("REPLAN_ON_EMPTY", "false").lower() in ("1","true","yes")
ESCALATE_ON_FAILURE = os.getenv("ESCALATE_ON_FAILURE", "false").lower() in ("1","true","yes")


def maybe_replan(trace_id: str, prompt: str, outputs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    if not ENABLE_REFLECTION:
        return []
    log_event(trace_id, "decision", "reflect:checkpoint", {"num_outputs": len(outputs)})
    if REPLAN_ON_EMPTY and not outputs:
        log_event(trace_id, "decision", "reflect:replan", {"reason": "empty_outputs"})
        # return a simple bootstrap step
        return [
            {"tool": "web_fetch", "args": {"url": "https://example.com"}},
        ]
    # Basic failure analysis: if most steps failed, suggest a template or delegate
    failures = sum(1 for o in outputs if isinstance(o, dict) and o.get("output") is None)
    if ESCALATE_ON_FAILURE and outputs and failures >= max(1, int(0.5 * len(outputs))):
        log_event(trace_id, "decision", "reflect:escalate", {"failures": failures})
        return [
            {"tool": "agent.delegate", "args": {"prompt": prompt, "tags": ["escalated"]}},
        ]
    return []