import importlib

from core.agentControl import plan_steps
import core.planning.advanced as adv


def test_plan_steps_rule_based(monkeypatch):
    monkeypatch.delenv("OLLAMA_HOST", raising=False)
    steps = plan_steps("Visit http://example.com and read report.pdf")
    assert steps == [
        {"tool": "web_fetch", "args": {"url": "https://example.com"}},
        {"tool": "pdf_text", "args": {"path": "./document.pdf"}},
    ]


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
