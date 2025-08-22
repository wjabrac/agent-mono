from typing import Any, Dict

from pydantic import BaseModel

from core.instrumentation import instrument_tool
from core.tools.registry import ToolSpec
from plugins.sandbox import run_in_sandbox


class SampleEchoInput(BaseModel):
    text: str = ""


class SampleEchoOutput(BaseModel):
    echo: str


@instrument_tool("sample_echo")
def _run(args: Dict[str, Any]) -> Dict[str, Any]:
    data = SampleEchoInput.model_validate(args)
    return SampleEchoOutput(echo=data.text).model_dump()


spec = ToolSpec(
    name="sample_echo",
    input_model=SampleEchoInput,
    output_model=SampleEchoOutput,
    run=run_in_sandbox(_run),
)
