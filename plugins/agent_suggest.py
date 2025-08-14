from core.instrumentation import instrument_tool
from core.llm import get_provider
from core.tools.registry import ToolSpec


def _provider():
    return get_provider({"provider": "gpt4all"})


@instrument_tool("agent_suggest_refactor")
def _refactor(args):
    code = args.get("code", "")
    prompt = f"Refactor the following code:\n{code}"
    suggestion = _provider().generate(prompt)
    return {"suggestion": suggestion}


@instrument_tool("agent_suggest_create")
def _create(args):
    text = args.get("prompt", "")
    prompt = f"Create helper code for:\n{text}"
    suggestion = _provider().generate(prompt)
    return {"suggestion": suggestion}


spec_refactor = ToolSpec(name="agent_suggest_refactor", input_model=None, run=_refactor)
spec_create = ToolSpec(name="agent_suggest_create", input_model=None, run=_create)
