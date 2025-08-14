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


class ThreadSafeCounter:
    """Prometheus ``Counter`` with an internal thread-safe snapshot."""

    def __init__(self, name: str, documentation: str, labelnames: List[str]):
        self._metric = Counter(name, documentation, labelnames)
        self._values: CounterDict[Tuple[str, ...]] = CounterDict()
        self._lock = threading.Lock()

    # ------------------------------------------------------------------
    def labels(self, *labelvalues: str) -> "_CounterChild":
        prom_child = self._metric.labels(*labelvalues)
        return _CounterChild(self, prom_child, tuple(labelvalues))

    def _inc(self, labelvalues: Tuple[str, ...], amount: float) -> None:
        with self._lock:
            self._values[labelvalues] += amount

    def export(self) -> Dict[str, Any]:
        """Return a JSON-serialisable snapshot of the counter values."""
        with self._lock:
            result: Dict[str, Any] = {}
            for labels, value in self._values.items():
                d = result
                for label in labels[:-1]:
                    d = d.setdefault(label, {})
                d[labels[-1]] = value
            return result

    def reset(self) -> None:
        """Clear all stored counter values."""
        with self._lock:
            self._values.clear()


class _CounterChild:
    def __init__(self, parent: ThreadSafeCounter, prom_child, labels: Tuple[str, ...]):
        self._parent = parent
        self._prom_child = prom_child
        self._labels = labels

    def inc(self, amount: float = 1.0) -> None:
        self._prom_child.inc(amount)
        self._parent._inc(self._labels, amount)


class ThreadSafeHistogram:
    """Prometheus ``Histogram`` with an internal thread-safe snapshot."""

    def __init__(self, name: str, documentation: str, labelnames: List[str]):
        self._metric = Histogram(name, documentation, labelnames)
        self._values: Dict[Tuple[str, ...], List[float]] = defaultdict(list)
        self._lock = threading.Lock()

    # ------------------------------------------------------------------
    def labels(self, *labelvalues: str) -> "_HistogramChild":
        prom_child = self._metric.labels(*labelvalues)
        return _HistogramChild(self, prom_child, tuple(labelvalues))

    def _observe(self, labelvalues: Tuple[str, ...], value: float) -> None:
        with self._lock:
            self._values[labelvalues].append(value)

    def export(self) -> Dict[str, Any]:
        """Return a JSON-serialisable snapshot of histogram observations."""
        with self._lock:
            result: Dict[str, Any] = {}
            for labels, values in self._values.items():
                d = result
                for label in labels[:-1]:
                    d = d.setdefault(label, {})
                d[labels[-1]] = list(values)
            return result

    def reset(self) -> None:
        """Clear all stored observations."""
        with self._lock:
            self._values.clear()


class _HistogramChild:
    def __init__(self, parent: ThreadSafeHistogram, prom_child, labels: Tuple[str, ...]):
        self._parent = parent
        self._prom_child = prom_child
        self._labels = labels

    def observe(self, value: float) -> None:
        self._prom_child.observe(value)
        self._parent._observe(self._labels, value)


# Module-level metrics -------------------------------------------------------

tool_calls_total = ThreadSafeCounter("tool_calls_total", "Tool calls", ["tool", "ok"])
tool_latency_ms = ThreadSafeHistogram("tool_latency_ms", "Tool latency (ms)", ["tool"])


def export() -> Dict[str, Any]:
    """Export a snapshot of all metrics."""
    return {
        "tool_calls_total": tool_calls_total.export(),
        "tool_latency_ms": tool_latency_ms.export(),
    }


def reset() -> None:
    """Reset all stored metric values."""
    tool_calls_total.reset()
    tool_latency_ms.reset()

