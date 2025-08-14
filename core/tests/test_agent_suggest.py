import types
import sys

from plugins import agent_suggest


def test_agent_suggest_offline(monkeypatch):
    class DummyGPT4All:
        def __init__(self, *a, **kw):
            pass

        def generate(self, prompt, **kw):
            return "ok"

    monkeypatch.setenv("LLM_PROVIDER", "gpt4all")
    import core.llm
    core.llm._PROVIDER = None  # reset singleton
    monkeypatch.setitem(sys.modules, "gpt4all", types.SimpleNamespace(GPT4All=DummyGPT4All))
    out = agent_suggest.spec_refactor.run({"code": "print(1)"})
    assert "ok" in out["suggestion"]
    out2 = agent_suggest.spec_create.run({"prompt": "add numbers"})
    assert "ok" in out2["suggestion"]
