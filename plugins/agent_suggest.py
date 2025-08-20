from typing import Any, Dict

from pydantic import BaseModel

from core.instrumentation import instrument_tool
from core.llm import get_provider
from core.tools.registry import ToolSpec
from plugins.sandbox import run_in_sandbox


def _provider():
    return get_provider({"provider": "gpt4all"})


class RefactorInput(BaseModel):
    code: str = ""


class CreateInput(BaseModel):
    prompt: str = ""


class SuggestOutput(BaseModel):
    suggestion: str


@instrument_tool("agent_suggest_refactor")
def _refactor(args: Dict[str, Any]) -> Dict[str, Any]:
    data = RefactorInput.model_validate(args)
    prompt = f"Refactor the following code:\n{data.code}"
    suggestion = _provider().generate(prompt)
    return SuggestOutput(suggestion=suggestion).model_dump()


@instrument_tool("agent_suggest_create")
def _create(args: Dict[str, Any]) -> Dict[str, Any]:
    data = CreateInput.model_validate(args)
    prompt = f"Create helper code for:\n{data.prompt}"
    suggestion = _provider().generate(prompt)
    return SuggestOutput(suggestion=suggestion).model_dump()


spec_refactor = ToolSpec(
    name="agent_suggest_refactor",
    input_model=RefactorInput,
    output_model=SuggestOutput,
    run=run_in_sandbox(_refactor),
)

spec_create = ToolSpec(
    name="agent_suggest_create",
    input_model=CreateInput,
    output_model=SuggestOutput,
    run=run_in_sandbox(_create),
)
