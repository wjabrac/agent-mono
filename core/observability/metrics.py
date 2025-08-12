
"""Lightweight in-memory metrics with tag support.

This module centralizes metric definitions without relying on external
services. Metrics are stored in dictionaries keyed by tag tuples, allowing
simple introspection while keeping runtime costs at zero.
"""

from collections import defaultdict
from typing import Dict, List, Tuple


class Counter:
    """A minimal counter supporting tag-based increments."""

    def __init__(self, name: str, description: str, label_names: List[str]):
        self.name = name
        self.description = description
        self.label_names = label_names
        self.values: Dict[Tuple[str, ...], float] = defaultdict(float)

    def labels(self, *label_values: str):
        key = tuple(label_values)
        parent = self

        class _LabeledCounter:
            def inc(self, amount: float = 1.0) -> None:
                parent.values[key] += amount

        return _LabeledCounter()


class Histogram:
    """A minimal histogram storing count and sum for observations."""

    def __init__(self, name: str, description: str, label_names: List[str]):
        self.name = name
        self.description = description
        self.label_names = label_names
        self.values: Dict[Tuple[str, ...], Dict[str, float]] = defaultdict(
            lambda: {"count": 0, "sum": 0.0}
        )

    def labels(self, *label_values: str):
        key = tuple(label_values)
        parent = self

        class _LabeledHistogram:
            def observe(self, value: float) -> None:
                bucket = parent.values[key]
                bucket["count"] += 1
                bucket["sum"] += value

        return _LabeledHistogram()


# Number of times a tool has been invoked along with whether the call succeeded.
tool_calls_total = Counter("tool_calls_total", "Tool calls", ["tool", "ok", "tags"])

# Latency of individual tool calls in milliseconds.
tool_latency_ms = Histogram("tool_latency_ms", "Tool latency (ms)", ["tool", "tags"])

# Total tokens consumed by each tool. This helps surface budget usage.
tool_tokens_total = Counter(
    "tool_tokens_total", "Tokens consumed by tool", ["tool", "tags"]
)
