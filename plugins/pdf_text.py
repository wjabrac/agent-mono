from typing import Dict, Any
from pydantic import BaseModel
from core.instrumentation import instrument_tool
from core.tools.registry import ToolSpec
import pdfminer.high_level as pdfminer
class PdfInput(BaseModel):
    path: str
@instrument_tool("pdf_text")
def _run(args: Dict[str, Any]) -> Dict[str, Any]:
    data = PdfInput(**args)
    text = pdfminer.extract_text(data.path)
    if not text.strip():
        raise RuntimeError("empty_text")
    return {"text": text}
pdf_text = ToolSpec(name="pdf_text", input_model=PdfInput, run=_run)
