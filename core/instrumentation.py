import functools, time
from typing import Callable, Dict, Any
from core.observability.trace import log_event, start_trace
from core.trace_context import current_thread_id, current_trace_id, current_tags
def instrument_tool(tool_name: str) -> Callable:
    def decorator(fn: Callable[[Dict[str, Any]], Dict[str, Any]]):
        @functools.wraps(fn)
        def wrapper(args: Dict[str, Any]) -> Dict[str, Any]:
            thread_id = current_thread_id.get()
            trace_id = current_trace_id.get()
            tags = current_tags.get()
            if not trace_id:
                trace_id = start_trace(thread_id)
            log_event(trace_id, "decision", "executor:start", {"tool": tool_name, "args": args, "tags": tags})
            t0 = time.time()
            try:
                out = fn(args)
                log_event(trace_id, "decision", "executor:done", {"tool": tool_name, "ms": int((time.time()-t0)*1000), "ok": True, "tags": tags})
                return out
            except Exception as e:
                log_event(trace_id, "decision", "executor:error", {"tool": tool_name, "ms": int((time.time()-t0)*1000), "ok": False, "error": type(e).__name__, "msg": str(e), "tags": tags})
                raise
        return wrapper
    return decorator
