import json
from typing import Any, Dict

from pydantic import BaseModel

from core.instrumentation import instrument_tool
from core.tools.registry import ToolSpec
from plugins.sandbox import run_in_sandbox


class JsonParseInput(BaseModel):
    text: str


class JsonParseOutput(BaseModel):
    json: Dict[str, Any]


@instrument_tool("json_parse")
def _run(args: Dict[str, Any]) -> Dict[str, Any]:
    data = JsonParseInput.model_validate(args)
    parsed = json.loads(data.text)
    return JsonParseOutput(json=parsed).model_dump()


spec = ToolSpec(
    name="json_parse",
    input_model=JsonParseInput,
    output_model=JsonParseOutput,
    run=run_in_sandbox(_run),
)
