from typing import Dict, Any
import json
from pydantic import BaseModel
from core.instrumentation import instrument_tool
from core.tools.registry import ToolSpec

class JsonInput(BaseModel):
	path: str
	max_bytes: int = 1024 * 1024

@instrument_tool("json_parse")
def _run(args: Dict[str, Any]) -> Dict[str, Any]:
	data = JsonInput(**args)
	with open(data.path, "r", encoding="utf-8", errors="ignore") as f:
		content = f.read(data.max_bytes)
	try:
		obj = json.loads(content)
	except Exception:
		obj = {"raw": content}
	return {"json": obj}

json_parse = ToolSpec(name="json_parse", input_model=JsonInput, run=_run)