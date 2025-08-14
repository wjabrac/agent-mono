import pytest
from prometheus_client import Counter, CollectorRegistry

from core.observability import metrics


def _setup_counter(monkeypatch):
    registry = CollectorRegistry()
    counter = Counter(
        "tool_requests_total", "Tool requests", ["tool", "found"], registry=registry
    )
    monkeypatch.setattr(metrics, "tool_requests_total", counter)
    return registry


def test_record_tool_request_found(monkeypatch):
    registry = _setup_counter(monkeypatch)

    # Simulate a tool existing in the registry
    monkeypatch.setattr(metrics.registry, "get", lambda name: object())

    metrics.record_tool_request("example")

    assert (
        registry.get_sample_value(
            "tool_requests_total", {"tool": "example", "found": "true"}
        )
        == 1
    )


def test_record_tool_request_missing(monkeypatch):
    registry = _setup_counter(monkeypatch)

    def _missing(name):
        raise KeyError(name)

    monkeypatch.setattr(metrics.registry, "get", _missing)

    with pytest.raises(KeyError):
        metrics.record_tool_request("missing")

    assert (
        registry.get_sample_value(
            "tool_requests_total", {"tool": "missing", "found": "false"}
        )
        == 1
    )
