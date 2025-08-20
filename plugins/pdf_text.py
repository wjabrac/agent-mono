import os
from typing import Any, Dict

from pydantic import BaseModel

from core.instrumentation import instrument_tool
from core.tools.registry import ToolSpec
from plugins.sandbox import run_in_sandbox


class PdfTextInput(BaseModel):
    path: str


class PdfTextOutput(BaseModel):
    bytes: int


@instrument_tool("pdf_text")
def _run(args: Dict[str, Any]) -> Dict[str, Any]:
    data = PdfTextInput.model_validate(args)
    path = data.path
    if not os.path.exists(path):
        raise FileNotFoundError("missing_or_invalid_path")
    with open(path, "rb") as f:
        data_bytes = f.read(100000)
    return PdfTextOutput(bytes=len(data_bytes)).model_dump()


spec = ToolSpec(
    name="pdf_text",
    input_model=PdfTextInput,
    output_model=PdfTextOutput,
    run=run_in_sandbox(_run),
)
