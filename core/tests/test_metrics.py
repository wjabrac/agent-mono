import pytest
from prometheus_client import Counter, CollectorRegistry

from core.observability import metrics


def _fresh_counter(monkeypatch):
    registry = CollectorRegistry()
    counter = Counter(
        "tool_requests_total", "Tool requests", ["tool", "found"], registry=registry
    )
    monkeypatch.setattr(metrics, "tool_requests_total", counter)
    return registry


def test_record_tool_request_found(monkeypatch):
    registry = _fresh_counter(monkeypatch)
    monkeypatch.setattr(metrics.registry, "get", lambda name: object())

    metrics.record_tool_request("echo")

    assert (
        registry.get_sample_value(
            "tool_requests_total", {"tool": "echo", "found": "true"}
        )
        == 1.0
    )


def test_record_tool_request_missing(monkeypatch):
    registry = _fresh_counter(monkeypatch)

    def fake_get(_name):
        raise KeyError("missing")

    monkeypatch.setattr(metrics.registry, "get", fake_get)

    with pytest.raises(KeyError):
        metrics.record_tool_request("ghost")

    assert (
        registry.get_sample_value(
            "tool_requests_total", {"tool": "ghost", "found": "false"}
        )
        == 1.0
    )
