from prometheus_client import Counter, Histogram

tool_calls_total = Counter("tool_calls_total", "Tool calls", ["tool", "ok"])
tool_latency_ms = Histogram("tool_latency_ms", "Tool latency (ms)", ["tool"])

tool_requests_total = Counter(
    "tool_requests_total",
    "Tool registry lookups",
    ["tool", "status"],
)


def record_tool_request(tool: str, status: str) -> None:
    """Record the outcome of a tool registry lookup."""
    tool_requests_total.labels(tool=tool, status=status).inc()
