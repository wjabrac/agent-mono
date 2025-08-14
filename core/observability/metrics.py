from typing import Dict, Tuple

# Try to use Prometheus if available for richer metrics and test compatibility
try:
    from prometheus_client import Counter as PromCounter, Histogram as PromHistogram  # type: ignore
    _PROM = True
except Exception:  # pragma: no cover - optional dep
    PromCounter = None  # type: ignore
    PromHistogram = None  # type: ignore
    _PROM = False


class _LabelledCounter:
    def __init__(self, store: Dict[Tuple[str, ...], int], label_values: Tuple[str, ...]):
        self._store = store
        self._label_values = label_values

    def inc(self, amount: int = 1) -> None:
        self._store[self._label_values] = self._store.get(self._label_values, 0) + amount


class _LabelledHistogram:
    def __init__(self, store: Dict[Tuple[str, ...], list], label_values: Tuple[str, ...]):
        self._store = store
        self._label_values = label_values

    def observe(self, value: float) -> None:
        self._store.setdefault(self._label_values, []).append(value)


class Counter:
    def __init__(self, name: str, description: str, labels: list[str]):
        self._name = name
        self._description = description
        self._labels = labels
        self._data: Dict[Tuple[str, ...], int] = {}

    def labels(self, *label_values: str):  # type: ignore[override]
        return _LabelledCounter(self._data, tuple(label_values))


class Histogram:
    def __init__(self, name: str, description: str, labels: list[str]):
        self._name = name
        self._description = description
        self._labels = labels
        self._data: Dict[Tuple[str, ...], list] = {}

    def labels(self, *label_values: str):  # type: ignore[override]
        return _LabelledHistogram(self._data, tuple(label_values))


# Prefer Prometheus-backed metrics if available
if _PROM:
    tool_calls_total = PromCounter("tool_calls_total", "Tool calls", ["tool", "ok"])  # type: ignore
    tool_latency_ms = PromHistogram("tool_latency_ms", "Tool latency (ms)", ["tool"])  # type: ignore
    tool_skipped_total = PromCounter("tool_skipped_total", "Tool skipped", ["tool", "reason"])  # type: ignore
    tool_requests_total = PromCounter("tool_requests_total", "Tool requests", ["tool", "status"])  # type: ignore
    llm_calls_total = PromCounter("llm_calls_total", "LLM calls", ["model", "ok", "tags"])  # type: ignore
    llm_latency_ms = PromHistogram("llm_latency_ms", "LLM latency (ms)", ["model", "tags"])  # type: ignore
else:  # lightweight in-process metrics
    tool_calls_total = Counter("tool_calls_total", "Tool calls", ["tool", "ok"])
    tool_latency_ms = Histogram("tool_latency_ms", "Tool latency (ms)", ["tool"])
    tool_skipped_total = Counter("tool_skipped_total", "Tool skipped", ["tool", "reason"])
    tool_requests_total = Counter("tool_requests_total", "Tool requests", ["tool", "status"])
    llm_calls_total = Counter("llm_calls_total", "LLM calls", ["model", "ok", "tags"])  # type: ignore
    llm_latency_ms = Histogram("llm_latency_ms", "LLM latency (ms)", ["model", "tags"])  # type: ignore


def record_tool_request(tool: str, status: str) -> None:
    """Record a tool lookup request."""
    tool_requests_total.labels(tool, status).inc()  # type: ignore[attr-defined]

