from prometheus_client import Counter, Histogram
tool_calls_total = Counter("tool_calls_total", "Tool calls", ["tool","ok"])
tool_latency_ms = Histogram("tool_latency_ms", "Tool latency (ms)", ["tool"])
