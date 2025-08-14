from prometheus_client import Counter, CollectorRegistry

from core.observability import metrics


def _fresh_counter(monkeypatch):
    registry = CollectorRegistry()
    counter = Counter(
        "tool_requests_total", "Tool requests", ["tool", "status"], registry=registry
    )
    monkeypatch.setattr(metrics, "tool_requests_total", counter)
    return registry


def test_record_tool_request_found(monkeypatch):
    registry = _fresh_counter(monkeypatch)

    metrics.record_tool_request("echo", "found")

    assert (
        registry.get_sample_value(
            "tool_requests_total", {"tool": "echo", "status": "found"}
        )
        == 1.0
    )


def test_record_tool_request_missing(monkeypatch):
    registry = _fresh_counter(monkeypatch)

    metrics.record_tool_request("ghost", "not_found")

    assert (
        registry.get_sample_value(
            "tool_requests_total", {"tool": "ghost", "status": "not_found"}
        )
        == 1.0
    )
