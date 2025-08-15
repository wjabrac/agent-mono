"""Minimal in-process metrics without external dependencies."""

from typing import Dict, Tuple


METRICS_BACKEND = "builtin"  # hard-disabled to avoid Prometheus


class _RegistryShim:
    def get(self, name: str):
        raise KeyError("missing")


registry = _RegistryShim()  # type: ignore


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

    def labels(self, *label_values: str):
        return _LabelledCounter(self._data, tuple(label_values))


class Histogram:
    def __init__(self, name: str, description: str, labels: list[str]):
        self._name = name
        self._description = description
        self._labels = labels
        self._data: Dict[Tuple[str, ...], list] = {}

    def labels(self, *label_values: str):
        return _LabelledHistogram(self._data, tuple(label_values))


# Built-in metrics only
tool_calls_total = Counter("tool_calls_total", "Tool calls", ["tool", "ok"])
tool_latency_ms = Histogram("tool_latency_ms", "Tool latency (ms)", ["tool"])
tool_skipped_total = Counter("tool_skipped_total", "Tool skipped", ["tool", "reason"])
tool_requests_total = Counter("tool_requests_total", "Tool requests", ["tool", "found"])
llm_calls_total = Counter("llm_calls_total", "LLM calls", ["model", "ok", "tags"])
llm_latency_ms = Histogram("llm_latency_ms", "LLM latency (ms)", ["model", "tags"])


def record_tool_request(tool_name: str, found: str | bool | None = None) -> None:
    """
    Record a tool lookup request.
    If found is None, probe registry.get(tool_name) and emit true/false accordingly.
    """
    if found is None:
        try:
            registry.get(tool_name)  # type: ignore[attr-defined]
            tool_requests_total.labels(tool_name, "true").inc()  # type: ignore[attr-defined]
        except KeyError:
            tool_requests_total.labels(tool_name, "false").inc()  # type: ignore[attr-defined]
            raise
        return
    val = "true" if (found is True) or str(found).lower() in {"1", "true", "yes", "found"} else "false"
    tool_requests_total.labels(tool_name, val).inc()  # type: ignore[attr-defined]


