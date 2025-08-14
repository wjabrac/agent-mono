from typing import Dict, Tuple

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
	def labels(self, *label_values: str) -> _LabelledCounter:
		return _LabelledCounter(self._data, tuple(label_values))

class Histogram:
	def __init__(self, name: str, description: str, labels: list[str]):
		self._name = name
		self._description = description
		self._labels = labels
		self._data: Dict[Tuple[str, ...], list] = {}
	def labels(self, *label_values: str) -> _LabelledHistogram:
		return _LabelledHistogram(self._data, tuple(label_values))

# Lightweight local telemetry stores
# Access the raw data if needed via these objects' _data attributes

tool_calls_total = Counter("tool_calls_total", "Tool calls", ["tool","ok"])
tool_latency_ms = Histogram("tool_latency_ms", "Tool latency (ms)", ["tool"])
