from typing import Dict, Tuple

# Try to use Prometheus if available for richer metrics and test compatibility
try:
	from prometheus_client import Counter as PromCounter, Histogram as PromHistogram  # type: ignore
	_PROM = True
except Exception:  # pragma: no cover - optional dep
	PromCounter = None  # type: ignore
	PromHistogram = None  # type: ignore
	_PROM = False

# Provide a registry shim that tests can monkeypatch
class _RegistryShim:
	def get(self, name: str):  # pragma: no cover - overridden in tests
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
	tool_calls_total = PromCounter("tool_calls_total", "Tool calls", ["tool","ok"])  # type: ignore
	tool_latency_ms = PromHistogram("tool_latency_ms", "Tool latency (ms)", ["tool"])  # type: ignore
	tool_skipped_total = PromCounter("tool_skipped_total", "Tool skipped", ["tool","reason"])  # type: ignore
	tool_requests_total = PromCounter("tool_requests_total", "Tool requests", ["tool","found"])  # type: ignore
	llm_calls_total = PromCounter("llm_calls_total", "LLM calls", ["model","ok","tags"])  # type: ignore
	llm_latency_ms = PromHistogram("llm_latency_ms", "LLM latency (ms)", ["model","tags"])  # type: ignore
else:  # lightweight in-process metrics
	tool_calls_total = Counter("tool_calls_total", "Tool calls", ["tool","ok"])
	tool_latency_ms = Histogram("tool_latency_ms", "Tool latency (ms)", ["tool"])
	tool_skipped_total = Counter("tool_skipped_total", "Tool skipped", ["tool","reason"])
	tool_requests_total = Counter("tool_requests_total", "Tool requests", ["tool","found"])
	llm_calls_total = Counter("llm_calls_total", "LLM calls", ["model","ok","tags"])  # type: ignore
	llm_latency_ms = Histogram("llm_latency_ms", "LLM latency (ms)", ["model","tags"])  # type: ignore


def record_tool_request(tool_name: str, found: str | None = None) -> None:
	"""Record a tool lookup request.
	
	If ``found`` is None, attempt to resolve the tool via ``metrics.registry.get``
	to determine existence. This behavior is compatible with tests that monkeypatch
	``metrics.registry.get`` to raise ``KeyError`` for missing tools.
	"""
	if found is None:
		try:
			registry.get(tool_name)  # type: ignore[attr-defined]
			tool_requests_total.labels(tool_name, "true").inc()  # type: ignore[attr-defined]
			return
		except KeyError:
			tool_requests_total.labels(tool_name, "false").inc()  # type: ignore[attr-defined]
			raise
	# explicit path
	val = "true" if str(found).lower() in ("1","true","yes") or found is True else "false"  # type: ignore
	tool_requests_total.labels(tool_name, val).inc()  # type: ignore[attr-defined]
