from __future__ import annotations
from typing import List
from opentelemetry import metrics as _ot_metrics
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader, ConsoleMetricExporter

# Local, free, vendor-neutral metrics pipeline
_reader = PeriodicExportingMetricReader(ConsoleMetricExporter())
_provider = MeterProvider(metric_readers=[_reader])
_ot_metrics.set_meter_provider(_provider)
_meter = _ot_metrics.get_meter("core.observability.metrics", "0.1.0")


class _CounterLabels:
    def __init__(self, inst, attrs):
        self._i = inst
        self._a = attrs
    def inc(self, amount: int = 1) -> None:
        self._i.add(amount, attributes=self._a)
    def observe(self, value: float) -> None:
        pass
    def record(self, value: float) -> None:
        pass


class _HistLabels:
    def __init__(self, inst, attrs):
        self._i = inst
        self._a = attrs
    def observe(self, value: float) -> None:
        self._i.record(value, attributes=self._a)
    def record(self, value: float) -> None:
        self._i.record(value, attributes=self._a)
    def inc(self, amount: int = 1) -> None:
        pass


class Counter:
    def __init__(self, name: str, description: str, labels: List[str]):
        self._labels = labels
        self._inst = _meter.create_counter(name, description=description)
    def labels(self, *label_values: str) -> _CounterLabels:
        attrs = {k: v for k, v in zip(self._labels, label_values)}
        return _CounterLabels(self._inst, attrs)


class Histogram:
    def __init__(self, name: str, description: str, labels: List[str]):
        self._labels = labels
        self._inst = _meter.create_histogram(name, description=description)
    def labels(self, *label_values: str) -> _HistLabels:
        attrs = {k: v for k, v in zip(self._labels, label_values)}
        return _HistLabels(self._inst, attrs)


# Instruments (names/labels unchanged)
tool_calls_total = Counter("tool_calls_total", "Tool calls", ["tool", "ok"])
tool_latency_ms = Histogram("tool_latency_ms", "Tool latency (ms)", ["tool"])
tool_skipped_total = Counter("tool_skipped_total", "Tool skipped", ["tool", "reason"])
tool_requests_total = Counter("tool_requests_total", "Tool registry lookups", ["tool", "found"])
llm_calls_total = Counter("llm_calls_total", "LLM calls", ["model", "ok", "tags"])
llm_latency_ms = Histogram("llm_latency_ms", "LLM latency (ms)", ["model", "tags"])


def record_tool_request(tool_name: str, found: bool) -> None:
    """Emit registry lookup outcome; label values preserved as 'true'/'false'."""
    tool_requests_total.labels(tool_name, "true" if found else "false").inc()


