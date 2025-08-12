from typing import Dict, Any, List

import time
from pydantic import BaseModel

from core.llm import get_provider
from core.tools.registry import discover, get
from core.trace_context import set_trace
from core.observability.metrics import tool_calls_total, tool_latency_ms
from core.observability.trace import log_event, start_trace
discover("plugins")
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
        log_event(
            trace_id,
            "decision",
            "planner:step",
            {"tool": s.tool, "args": s.args, "tags": tags or []},
        )

        t0 = time.time()
        try:
            if s.tool in {"llm", "__llm__"}:
                prompt_text = s.args.get("prompt", prompt)
                other = {k: v for k, v in s.args.items() if k != "prompt"}
                text = provider.generate(prompt_text, **other)
                res = {"text": text}
            else:
                spec = get(s.tool)
                res = spec.run(s.args)

            tag_str = ",".join(tags or [])
            tool_calls_total.labels(s.tool, "true", tag_str).inc()
            tool_latency_ms.labels(s.tool, tag_str).observe((time.time() - t0) * 1000.0)
            log_event(
                trace_id,
                "decision",
                "tool:done",
                {
                    "tool": s.tool,
                    "ms": int((time.time() - t0) * 1000),
                    "tags": tags or [],
                },
            )
            out.append({"tool": s.tool, "output": res})
        except Exception as e:
            tag_str = ",".join(tags or [])
            tool_calls_total.labels(s.tool, "false", tag_str).inc()
            log_event(
                trace_id,
                "decision",
                "tool:error",
                {
                    "tool": s.tool,
                    "ms": int((time.time() - t0) * 1000),
                    "error": str(e),
                    "tags": tags or [],
                },
            )
            raise

    return {"trace_id": trace_id, "outputs": out}
