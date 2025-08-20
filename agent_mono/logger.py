from __future__ import annotations
import json, threading, time
from typing import Any, Dict

_COUNTERS: Dict[str, int] = {}
_LOCK = threading.Lock()

def log_event(event: str, **data: Any) -> None:
    with _LOCK:
        _COUNTERS[event] = _COUNTERS.get(event, 0) + 1
        record = {"ts": time.time(), "event": event, "count": _COUNTERS[event], **data}
        print(json.dumps(record, sort_keys=True))
