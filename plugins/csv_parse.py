import csv
from io import StringIO
from typing import Any, Dict, List

from pydantic import BaseModel

from core.instrumentation import instrument_tool
from core.tools.registry import ToolSpec
from plugins.sandbox import run_in_sandbox


class CsvParseInput(BaseModel):
    text: str


class CsvParseOutput(BaseModel):
    rows: List[Dict[str, str]]


@instrument_tool("csv_parse")
def _run(args: Dict[str, Any]) -> Dict[str, Any]:
    data = CsvParseInput.model_validate(args)
    reader = csv.DictReader(StringIO(data.text))
    rows = list(reader)
    return CsvParseOutput(rows=rows).model_dump()


spec = ToolSpec(
    name="csv_parse",
    input_model=CsvParseInput,
    output_model=CsvParseOutput,
    run=run_in_sandbox(_run),
)
