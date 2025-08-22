import importlib

import core.planning.advanced as adv


def _reload_adv(monkeypatch):
    monkeypatch.setenv("ADVANCED_PLANNING", "true")
    importlib.reload(adv)
    return adv


def test_if_else_expansion(monkeypatch):
    mod = _reload_adv(monkeypatch)
    plan = [{"if": True, "then": [{"tool": "a", "args": {}}], "else": [{"tool": "b", "args": {}}]}]
    assert mod.expand_plan(plan) == [{"tool": "a", "args": {}}]


def test_loop_and_while_expansion(monkeypatch):
    mod = _reload_adv(monkeypatch)
    plan = [
        {"loop": {"times": 2}, "steps": [{"tool": "a", "args": {}}]},
        {"while": {"cond": True, "max": 2}, "steps": [{"tool": "b", "args": {}}]},
    ]
    expanded = mod.expand_plan(plan)
    assert expanded == [
        {"tool": "a", "args": {}},
        {"tool": "a", "args": {}},
        {"tool": "b", "args": {}},
        {"tool": "b", "args": {}},
    ]
