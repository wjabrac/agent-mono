from typing import Dict, Any, List
from pydantic import BaseModel
from core.tools.registry import discover, get
from core.trace_context import set_trace
from core.observability.trace import start_trace, log_event
from core.observability.metrics import (
    tool_calls_total,
    tool_latency_ms,
    tool_tokens_total,
)
import time
discover("plugins")
class Step(BaseModel):
    tool: str
    args: Dict[str, Any]
def execute_steps(prompt: str, steps: List[Dict[str, Any]], thread_id=None, tags=None) -> Dict[str, Any]:
    trace_id = start_trace(thread_id)
    set_trace(thread_id, trace_id, tags or [])
    label_tags = ",".join(sorted(tags or []))
    out = []
    for st in steps:
        s = Step(**st)
        log_event(
            trace_id,
            "decision",
            "planner:step",
            {"tool": s.tool, "args": s.args, "tags": tags or []},
        )
        spec = get(s.tool)
        t0 = time.time()
        ok = "true"
        tokens = 0
        try:
            res = spec.run(s.args)
            # Attempt to extract token usage for budget tracking.
            if isinstance(res, dict):
                usage = res.get("usage") or {}
                tokens = (
                    usage.get("total_tokens")
                    or res.get("total_tokens")
                    or res.get("token_usage", 0)
                )
            out.append({"tool": s.tool, "output": res})
        except Exception:
            ok = "false"
            raise
        finally:
            tool_calls_total.labels(s.tool, ok, label_tags).inc()
            tool_latency_ms.labels(s.tool, label_tags).observe((time.time() - t0) * 1000.0)
            if tokens:
                tool_tokens_total.labels(s.tool, label_tags).inc(tokens)
    return {"trace_id": trace_id, "outputs": out}
