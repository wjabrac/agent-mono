from typing import Any, Dict

from pydantic import BaseModel, HttpUrl

from core.instrumentation import instrument_tool
from core.tools.registry import ToolSpec
from plugins.sandbox import run_in_sandbox


class WebFetchInput(BaseModel):
    url: HttpUrl


class WebFetchOutput(BaseModel):
    text: str


@instrument_tool("web_fetch")
def _run(args: Dict[str, Any]) -> Dict[str, Any]:
    data = WebFetchInput.model_validate(args)
    try:
        import httpx
    except ImportError as e:  # pragma: no cover - import guarded
        raise RuntimeError("httpx extra is not installed") from e
    r = httpx.get(str(data.url), timeout=15)
    r.raise_for_status()
    return WebFetchOutput(text=r.text[:10000]).model_dump()


spec = ToolSpec(
    name="web_fetch",
    input_model=WebFetchInput,
    output_model=WebFetchOutput,
    run=run_in_sandbox(_run),
)
