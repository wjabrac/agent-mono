from core.instrumentation import instrument_tool
from core.tools.registry import ToolSpec


@instrument_tool("image_info")
def _run(args):
        path = args.get("path")
        if not path:
                return {"width": 0, "height": 0}
        try:
                from PIL import Image  # type: ignore
        except ImportError as e:  # pragma: no cover - import guarded
                raise RuntimeError("pillow extra is not installed") from e
        im = Image.open(path)
        return {"width": im.width, "height": im.height}

spec = ToolSpec(name="image_info", input_model=None, run=_run)