from typing import Dict, Any, List
from pydantic import BaseModel
from core.tools.registry import discover, get
from core.trace_context import set_trace
from core.observability.trace import start_trace, log_event
from core.observability.metrics import tool_calls_total, tool_latency_ms, tool_skipped_total
import time

discover("plugins")

class Step(BaseModel):
    tool: str
    args: Dict[str, Any]

def execute_steps(prompt: str, steps: List[Dict[str, Any]], thread_id=None, tags=None) -> Dict[str, Any]:
    trace_id = start_trace(thread_id)
    set_trace(thread_id, trace_id, tags or [])
    out = []
    total = len(steps)
    for idx, st in enumerate(steps):
        s = Step(**st)
        log_event(trace_id, "decision", "planner:step", {"tool": s.tool, "args": s.args, "tags": tags or []})
        try:
            spec = get(s.tool)
        except KeyError:
            tool_skipped_total.labels(s.tool, "not_found").inc()
            log_event(trace_id, "decision", "executor:skip", {"tool": s.tool, "reason": "not_found", "args": s.args})
            continue
        t0 = time.time()
        try:
            res = spec.run(s.args)
            tool_calls_total.labels(s.tool, "true").inc()
            tool_latency_ms.labels(s.tool).observe((time.time()-t0)*1000.0)
            out.append({"tool": s.tool, "output": res})
        except Exception as e:
            tool_calls_total.labels(s.tool, "false").inc()
            log_event(trace_id, "decision", "executor:error", {"tool": s.tool, "error": type(e).__name__, "msg": str(e)})
            # mark remaining steps as skipped due to prior error
            for rem in steps[idx+1:]:
                try:
                    rem_name = Step(**rem).tool
                except Exception:
                    rem_name = rem.get("tool", "<unknown>") if isinstance(rem, dict) else "<unknown>"
                tool_skipped_total.labels(rem_name, "prior_error").inc()
                log_event(trace_id, "decision", "executor:skip", {"tool": rem_name, "reason": "prior_error"})
            raise
    return {"trace_id": trace_id, "outputs": out}
