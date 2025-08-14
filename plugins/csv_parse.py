import csv
from io import StringIO
from core.instrumentation import instrument_tool
from core.tools.registry import ToolSpec


@instrument_tool("csv_parse")
def _run(args):
	text = args.get("text", "")
	reader = csv.DictReader(StringIO(text))
	return {"rows": list(reader)}

spec = ToolSpec(name="csv_parse", input_model=None, run=_run)