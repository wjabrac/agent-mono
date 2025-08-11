import contextvars
from typing import List, Optional
current_thread_id = contextvars.ContextVar("current_thread_id", default=None)  # type: ignore
current_trace_id = contextvars.ContextVar("current_trace_id", default=None)    # type: ignore
current_tags = contextvars.ContextVar("current_tags", default=[])              # type: ignore
def set_trace(thread_id: Optional[str], trace_id: Optional[str], tags: Optional[List[str]] = None) -> None:
    if thread_id is not None: current_thread_id.set(thread_id)
    if trace_id is not None: current_trace_id.set(trace_id)
    if tags is not None: current_tags.set(tags)
