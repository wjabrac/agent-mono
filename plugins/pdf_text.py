import os
from core.instrumentation import instrument_tool
from core.tools.registry import ToolSpec


@instrument_tool("pdf_text")
def _run(args):
	path = args.get("path")
	if not path or not os.path.exists(path):
		raise FileNotFoundError("missing_or_invalid_path")
	# For brevity, read binary and return stub since heavy parsing libs exist in libs/
	with open(path, "rb") as f:
		data = f.read(100000)
	return {"bytes": len(data)}

spec = ToolSpec(name="pdf_text", input_model=None, run=_run)
