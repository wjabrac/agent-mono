from core.instrumentation import instrument_tool
from core.tools.registry import ToolSpec

try:
	from PIL import Image  # type: ignore
except Exception:
	Image = None  # type: ignore


@instrument_tool("image_info")
def _run(args):
	path = args.get("path")
	if not path or Image is None:
		return {"width": 0, "height": 0}
	im = Image.open(path)
	return {"width": im.width, "height": im.height}

spec = ToolSpec(name="image_info", input_model=None, run=_run)