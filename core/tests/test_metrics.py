import pytest
from core.observability import metrics


def _fresh_counter(monkeypatch):
    counter = metrics.Counter("tool_requests_total", "Tool requests", ["tool", "found"])
    monkeypatch.setattr(metrics, "tool_requests_total", counter)
    return counter


def test_record_tool_request_found(monkeypatch):
    counter = _fresh_counter(monkeypatch)
    monkeypatch.setattr(metrics.registry, "get", lambda name: object())
    metrics.record_tool_request("echo")          # probe path
    metrics.record_tool_request("echo", "true")  # explicit path
    assert counter._data[("echo", "true")] == 2


def test_record_tool_request_missing(monkeypatch):
    counter = _fresh_counter(monkeypatch)

    def fake_get(_name):
        raise KeyError("missing")

    monkeypatch.setattr(metrics.registry, "get", fake_get)
    with pytest.raises(KeyError):
        metrics.record_tool_request("ghost")     # probe path raises
    metrics.record_tool_request("ghost", "false")  # explicit path
    assert counter._data[("ghost", "false")] == 2


