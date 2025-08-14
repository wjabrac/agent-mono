from typing import Dict, Any, List

import time
from pydantic import BaseModel

from core.llm import get_provider
from core.tools.registry import discover, get
from core.trace_context import set_trace
from core.observability.metrics import tool_calls_total, tool_latency_ms
from core.observability.trace import log_event, start_trace
discover("plugins")
budget_manager = get_budget_manager()
class Step(BaseModel):
    tool: str
    args: Dict[str, Any]
def execute_steps(prompt: str, steps: List[Dict[str, Any]], thread_id=None, tags=None) -> Dict[str, Any]:
    """Execute a series of steps using the configured LLM provider and tools."""

    trace_id = start_trace(thread_id)
    set_trace(thread_id, trace_id, tags or [])
    provider = get_provider()

    out: List[Dict[str, Any]] = []
    for st in steps:
        s = Step(**st)
        log_event(trace_id, "decision", "planner:step", {"tool": s.tool, "args": s.args, "tags": tags or []})
        try:
            spec = get(s.tool)
        except KeyError:
            log_event(trace_id, "decision", "tool:lookup_error", {"tool": s.tool, "args": s.args, "tags": tags or []})
            raise
        t0 = time.time()
        ok = "true"
        tokens = 0
        try:
            res = spec.run(s.args)
            tool_calls_total.labels(s.tool, "true").inc()
            tool_latency_ms.labels(s.tool).observe((time.time()-t0)*1000.0)
            log_event(trace_id, "decision", "tool:result", {"tool": s.tool, "ms": int((time.time()-t0)*1000), "ok": True, "output": res})
            out.append({"tool": s.tool, "output": res})
        except Exception as e:
            tool_calls_total.labels(s.tool, "false").inc()
            log_event(trace_id, "decision", "tool:result", {"tool": s.tool, "ms": int((time.time()-t0)*1000), "ok": False, "error": type(e).__name__, "msg": str(e)})
            raise

    return {"trace_id": trace_id, "outputs": out}
