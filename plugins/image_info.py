from typing import Dict, Any
from pydantic import BaseModel
from core.instrumentation import instrument_tool
from core.tools.registry import ToolSpec

try:
	from PIL import Image  # type: ignore
except Exception:
	Image = None  # type: ignore

class ImageInput(BaseModel):
	path: str

@instrument_tool("image_info")
def _run(args: Dict[str, Any]) -> Dict[str, Any]:
	data = ImageInput(**args)
	if Image is None:
		raise RuntimeError("pillow_not_installed")
	im = Image.open(data.path)
	return {"format": im.format, "size": im.size, "mode": im.mode}

image_info = ToolSpec(name="image_info", input_model=ImageInput, run=_run)