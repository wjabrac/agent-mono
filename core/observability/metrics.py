"""Thread-safe in-process metrics helpers.

This module wraps ``prometheus_client`` metrics with lightweight data
structures that keep an in-memory snapshot of metric values.  The snapshot can
be exported as JSON-serialisable data and reset between tests or runs.

Two metrics are exposed:

``tool_calls_total``
    Counter tracking the number of tool invocations labelled by tool name and
    success flag.

``tool_latency_ms``
    Histogram storing the latency of tool invocations in milliseconds labelled
    by tool name.

The helpers are intentionally minimal and only implement the parts of the
Prometheus API that are currently used within the code base.
"""

from __future__ import annotations

from collections import Counter as CounterDict, defaultdict
import threading
from typing import Any, Dict, List, Tuple

from prometheus_client import Counter, Histogram
from core.tools import registry

tool_calls_total = Counter("tool_calls_total", "Tool calls", ["tool", "ok"])
tool_latency_ms = Histogram("tool_latency_ms", "Tool latency (ms)", ["tool"])

tool_requests_total = Counter(
    "tool_requests_total", "Tool requests", ["tool", "found"]
)


def record_tool_request(tool_name: str) -> None:
    """Record that a tool was requested.

    Increments the ``tool_requests_total`` counter with ``found`` set to
    ``"true"`` when the tool exists in the registry or ``"false"`` when the
    registry lookup raises ``KeyError``. The ``KeyError`` is re-raised so the
    caller can handle the missing tool case.
    """

    try:
        registry.get(tool_name)
    except KeyError:
        tool_requests_total.labels(tool=tool_name, found="false").inc()
        raise
    else:
        tool_requests_total.labels(tool=tool_name, found="true").inc()
