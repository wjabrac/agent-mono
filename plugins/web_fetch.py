from typing import Dict, Any
import requests
from pydantic import BaseModel
from core.instrumentation import instrument_tool
from core.tools.registry import ToolSpec
class FetchInput(BaseModel):
    url: str
    timeout: int = 15
@instrument_tool("web_fetch")
def _run(args: Dict[str, Any]) -> Dict[str, Any]:
    data = FetchInput(**args)
    r = requests.get(data.url, timeout=data.timeout)
    r.raise_for_status()
    return {"text": r.text[:200000]}
web_fetch = ToolSpec(name="web_fetch", input_model=FetchInput, run=_run)
