import importlib

import sys
import types

class _Span:
    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def set_attribute(self, *args, **kwargs):
        pass

class _Tracer:
    def start_as_current_span(self, *a, **k):
        return _Span()

_trace_stub = types.SimpleNamespace(get_tracer=lambda *a, **k: _Tracer())

class _DummyInstrument:
    def add(self, *a, **k):
        pass

    def record(self, *a, **k):
        pass

class _DummyMeter:
    def create_counter(self, *a, **k):
        return _DummyInstrument()

    def create_histogram(self, *a, **k):
        return _DummyInstrument()

_metrics_stub = types.SimpleNamespace(
    set_meter_provider=lambda *a, **k: None,
    get_meter=lambda *a, **k: _DummyMeter(),
)
sys.modules.setdefault("opentelemetry.trace", _trace_stub)
sys.modules.setdefault("opentelemetry.metrics", _metrics_stub)
sys.modules.setdefault(
    "opentelemetry", types.SimpleNamespace(trace=_trace_stub, metrics=_metrics_stub)
)
class _dummy:  # minimal callable class
    def __init__(self, *a, **k):
        pass
_export = types.SimpleNamespace(
    PeriodicExportingMetricReader=_dummy, ConsoleMetricExporter=_dummy
)
sys.modules.setdefault("opentelemetry.sdk", types.SimpleNamespace())
sys.modules.setdefault(
    "opentelemetry.sdk.metrics",
    types.SimpleNamespace(MeterProvider=_dummy, export=_export),
)
sys.modules.setdefault("opentelemetry.sdk.metrics.export", _export)
plugins_mod = types.ModuleType("plugins")
plugins_mod.__path__ = []
sys.modules.setdefault("plugins", plugins_mod)

from core.agentControl import plan_steps
import core.agentControl as ac
import core.planning.advanced as adv


def test_plan_steps_rule_based(monkeypatch):
    monkeypatch.setattr(ac, "httpx", None, raising=True)
    monkeypatch.setattr(ac, "_llm_plan", lambda prompt: [])
    steps = plan_steps("Visit http://example.com and read report.pdf")
    assert steps == [
        {"tool": "web_fetch", "args": {"url": "https://example.com"}},
        {"tool": "pdf_text", "args": {"path": "./document.pdf"}},
    ]


def test_plan_steps_llm_provider(monkeypatch):
    monkeypatch.setattr(ac, "httpx", None, raising=True)

    class _Prov:
        def generate(self, prompt: str, **kwargs):
            return '[{"tool": "web_fetch", "args": {"url": "https://example.com"}}]'

    monkeypatch.setattr("core.agentControl.get_provider", lambda: _Prov())
    steps = plan_steps("Visit http://example.com")
    assert steps == [{"tool": "web_fetch", "args": {"url": "https://example.com"}}]


def test_plan_steps_ollama_path(monkeypatch):
    import json as _json

    class _Resp:
        def __init__(self, payload):
            self._p = payload

        def raise_for_status(self):
            return None

        def json(self):
            return self._p

    def _post(url, json, timeout):
        return _Resp({"response": _json.dumps([{"tool": "pdf_text", "args": {"path": "./document.pdf"}}])})

    fake_httpx = types.SimpleNamespace(post=_post)
    monkeypatch.setattr(ac, "httpx", fake_httpx, raising=True)
    steps = plan_steps("parse .pdf")
    assert steps == [{"tool": "pdf_text", "args": {"path": "./document.pdf"}}]


def test_expand_plan_behaviors(monkeypatch):
    monkeypatch.setenv("ADVANCED_PLANNING", "false")
    importlib.reload(adv)
    raw = [{"tool": "web_fetch", "args": {"url": "https://example.com"}}]
    assert adv.expand_plan(raw) == raw

    monkeypatch.setenv("ADVANCED_PLANNING", "true")
    importlib.reload(adv)
    plan = [
        {
            "if": False,
            "then": [{"tool": "web_fetch", "args": {"url": "1"}}],
            "else": [{"tool": "web_fetch", "args": {"url": "2"}}],
        },
        {
            "loop": {"times": 2},
            "steps": [{"tool": "pdf_text", "args": {"path": "./document.pdf"}}],
        },
        {
            "retry": {"max": 2},
            "steps": [{"tool": "sample_echo", "args": {"text": "hi"}}],
        },
        {
            "while": {"cond": True, "max": 1},
            "steps": [{"tool": "sample_echo", "args": {"text": "x"}}],
        },
    ]
    expanded = adv.expand_plan(plan)
    assert [s["tool"] for s in expanded] == [
        "web_fetch",
        "pdf_text",
        "pdf_text",
        "sample_echo",
        "sample_echo",
        "sample_echo",
    ]
