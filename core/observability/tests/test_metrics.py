import threading
import pathlib
import sys

# Ensure repository root is on the Python path when tests are executed directly
ROOT = pathlib.Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from core.observability import metrics


def test_export_format() -> None:
    metrics.reset()
    metrics.tool_calls_total.labels("sample", "true").inc()
    metrics.tool_latency_ms.labels("sample").observe(5.0)

    snapshot = metrics.export()
    assert snapshot["tool_calls_total"]["sample"]["true"] == 1
    assert snapshot["tool_latency_ms"]["sample"] == [5.0]


def test_thread_safety() -> None:
    metrics.reset()

    def worker() -> None:
        for _ in range(1000):
            metrics.tool_calls_total.labels("worker", "true").inc()
            metrics.tool_latency_ms.labels("worker").observe(1.0)

    threads = [threading.Thread(target=worker) for _ in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    snapshot = metrics.export()
    assert snapshot["tool_calls_total"]["worker"]["true"] == 10000
    assert len(snapshot["tool_latency_ms"]["worker"]) == 10000

