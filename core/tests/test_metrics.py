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

    class FoundRegistry:
        def get(self, name):
            return object()

    monkeypatch.setattr(metrics, "registry", FoundRegistry())

    metrics.record_tool_request("echo")

    assert (
        registry.get_sample_value(
            "tool_requests_total", {"tool": "echo", "found": "true"}
        )
        == 1.0
    )


def test_record_tool_request_missing(monkeypatch):
    registry = _fresh_counter(monkeypatch)

    class MissingRegistry:
        def get(self, name):
            raise KeyError("missing")

    monkeypatch.setattr(metrics, "registry", MissingRegistry())

    with pytest.raises(KeyError):
        metrics.record_tool_request("ghost")

    assert (
        registry.get_sample_value(
            "tool_requests_total", {"tool": "ghost", "found": "false"}
        )
        == 1.0
    )
