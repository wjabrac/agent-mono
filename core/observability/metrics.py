"""Lightweight in-process metrics helpers.

This module provides a very small subset of the Prometheus client API so the
rest of the codebase can track counters and histograms without depending on the
real ``prometheus_client`` package or a running Prometheus server.  Metrics are
stored in simple in-memory dictionaries keyed by the label values.  They are
primarily useful for debugging or unit tests where quick visibility into counts
and timings is sufficient.

Example::

    calls = Counter("my_calls", "Number of calls", ["name"])
    calls.labels("foo").inc()

    latency = Histogram("latency_ms", "Latency (ms)", ["name"])
    latency.labels("foo").observe(123.4)

The ``labels`` call returns a small handle object exposing ``inc`` or
``observe`` depending on metric type.  Collected values can be inspected via the
``data`` attribute on each metric instance.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import DefaultDict, Dict, Iterable, Tuple, List


# ---------------------------------------------------------------------------
# Metric base classes


@dataclass
class _CounterHandle:
    _store: DefaultDict[Tuple[str, ...], int]
    _key: Tuple[str, ...]

    def inc(self, value: int = 1) -> None:
        self._store[self._key] += value


@dataclass
class _HistogramHandle:
    _store: DefaultDict[Tuple[str, ...], List[float]]
    _key: Tuple[str, ...]

    def observe(self, value: float) -> None:
        self._store[self._key].append(float(value))


class Counter:
    """Minimal counter implementation with label support."""

    def __init__(self, name: str, doc: str, label_names: Iterable[str]):
        self.name = name
        self.documentation = doc
        self.label_names = list(label_names)
        self.data: DefaultDict[Tuple[str, ...], int] = defaultdict(int)

    def labels(self, *label_values: str) -> _CounterHandle:
        if len(label_values) != len(self.label_names):
            raise ValueError("label count mismatch")
        return _CounterHandle(self.data, tuple(label_values))


class Histogram:
    """Minimal histogram implementation with label support."""

    def __init__(self, name: str, doc: str, label_names: Iterable[str]):
        self.name = name
        self.documentation = doc
        self.label_names = list(label_names)
        self.data: DefaultDict[Tuple[str, ...], List[float]] = defaultdict(list)

    def labels(self, *label_values: str) -> _HistogramHandle:
        if len(label_values) != len(self.label_names):
            raise ValueError("label count mismatch")
        return _HistogramHandle(self.data, tuple(label_values))


# ---------------------------------------------------------------------------
# Predefined metrics used throughout the project.  We include a ``tags`` label
# so metrics can be filtered by high-level tags associated with a given trace or
# request.


tool_calls_total = Counter("tool_calls_total", "Tool calls", ["tool", "ok", "tags"])
tool_latency_ms = Histogram("tool_latency_ms", "Tool latency (ms)", ["tool", "tags"])

llm_calls_total = Counter("llm_calls_total", "LLM generation calls", ["model", "ok", "tags"])
llm_latency_ms = Histogram("llm_latency_ms", "LLM generation latency (ms)", ["model", "tags"])


__all__ = [
    "Counter",
    "Histogram",
    "tool_calls_total",
    "tool_latency_ms",
    "llm_calls_total",
    "llm_latency_ms",
]

