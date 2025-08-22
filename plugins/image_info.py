from typing import Any, Dict

from pydantic import BaseModel

from core.instrumentation import instrument_tool
from core.tools.registry import ToolSpec
from plugins.sandbox import run_in_sandbox


class ImageInfoInput(BaseModel):
    path: str


class ImageInfoOutput(BaseModel):
    width: int
    height: int


@instrument_tool("image_info")
def _run(args: Dict[str, Any]) -> Dict[str, Any]:
    data = ImageInfoInput.model_validate(args)
    path = data.path
    if not path:
        return ImageInfoOutput(width=0, height=0).model_dump()
    try:
        from PIL import Image  # type: ignore
    except ImportError as e:  # pragma: no cover - import guarded
        raise RuntimeError("pillow extra is not installed") from e
    im = Image.open(path)
    return ImageInfoOutput(width=im.width, height=im.height).model_dump()


spec = ToolSpec(
    name="image_info",
    input_model=ImageInfoInput,
    output_model=ImageInfoOutput,
    run=run_in_sandbox(_run),
)
