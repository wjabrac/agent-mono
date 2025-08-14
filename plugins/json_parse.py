import json
from core.instrumentation import instrument_tool
from core.tools.registry import ToolSpec


@instrument_tool("json_parse")
def _run(args):
	text = args.get("text", "")
	return {"json": json.loads(text)}

spec = ToolSpec(name="json_parse", input_model=None, run=_run)