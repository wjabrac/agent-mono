from typing import Dict, Any, List
from pydantic import BaseModel
from core.tools.registry import discover, get
from core.trace_context import set_trace
from core.observability.trace import start_trace, log_event
from core.observability.metrics import tool_calls_total, tool_latency_ms
import time
discover("plugins")
class Step(BaseModel):
    tool: str
    args: Dict[str, Any]
def execute_steps(prompt: str, steps: List[Dict[str, Any]], thread_id=None, tags=None) -> Dict[str, Any]:
    trace_id = start_trace(thread_id)
    set_trace(thread_id, trace_id, tags or [])
    out = []
    for st in steps:
        s = Step(**st)
        log_event(trace_id, "decision", "planner:step", {"tool": s.tool, "args": s.args, "tags": tags or []})
        try:
            spec = get(s.tool)
        except KeyError:
            log_event(trace_id, "decision", "tool:lookup_error", {"tool": s.tool, "tags": tags or []})
            raise
        t0 = time.time()
        try:
            res = spec.run(s.args)
            ms = (time.time()-t0)*1000.0
            tool_calls_total.labels(s.tool, "true").inc()
            tool_latency_ms.labels(s.tool).observe(ms)
            log_event(trace_id, "decision", "tool:result", {"tool": s.tool, "ms": int(ms), "ok": True, "output": res, "tags": tags or []})
            out.append({"tool": s.tool, "output": res})
        except Exception as e:
            ms = (time.time()-t0)*1000.0
            log_event(trace_id, "decision", "tool:result", {"tool": s.tool, "ms": int(ms), "ok": False, "error": type(e).__name__, "msg": str(e), "tags": tags or []})
            tool_calls_total.labels(s.tool, "false").inc()
            raise
    return {"trace_id": trace_id, "outputs": out}
