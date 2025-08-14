from core.tools.registry import ToolSpec
from core.instrumentation import instrument_tool

@instrument_tool("sample_echo")
def _run(args):
    text = args.get("text", "")
    return {"echo": text}

spec = ToolSpec(name="sample_echo", input_model=None, run=_run)
