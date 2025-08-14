"""Prometheus metrics helpers."""

from prometheus_client import Counter, Histogram

from core.tools import registry


# Metric tracking the total number of tool calls and their success.
tool_calls_total = Counter("tool_calls_total", "Tool calls", ["tool", "ok"])
tool_latency_ms = Histogram("tool_latency_ms", "Tool latency (ms)", ["tool"])

# Metric tracking whether a requested tool was found in the registry.
tool_requests_total = Counter(
    "tool_requests_total", "Tool requests", ["tool", "found"],
)


def record_tool_request(name: str) -> None:
    """Record a request for a tool.

    Parameters
    ----------
    name:
        The name of the tool being requested.

    The function consults the global tool ``registry``.  If the tool exists the
    counter is incremented with ``found=true``.  If the tool is missing the
    counter is incremented with ``found=false`` and the ``KeyError`` is re-raised
    so callers can handle the missing tool appropriately.
    """

    try:
        registry.get(name)
    except KeyError:
        # Increment metric for missing tools before propagating the error.
        tool_requests_total.labels(tool=name, found="false").inc()
        raise
    else:
        # Tool found in registry.
        tool_requests_total.labels(tool=name, found="true").inc()

