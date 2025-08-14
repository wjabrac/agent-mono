from typing import Dict, Any, List
import csv
from pydantic import BaseModel
from core.instrumentation import instrument_tool
from core.tools.registry import ToolSpec

class CsvInput(BaseModel):
    path: str
    limit: int = 1000

@instrument_tool("csv_parse")
def _run(args: Dict[str, Any]) -> Dict[str, Any]:
    data = CsvInput(**args)
    rows: List[List[str]] = []
    with open(data.path, newline="", encoding="utf-8", errors="ignore") as f:
        reader = csv.reader(f)
        for i, row in enumerate(reader):
            if i >= data.limit:
                break
            rows.append(row)
    return {"rows": rows}

csv_parse = ToolSpec(name="csv_parse", input_model=CsvInput, run=_run)