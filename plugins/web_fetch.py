import json
from core.tools.registry import ToolSpec
from core.instrumentation import instrument_tool


@instrument_tool("web_fetch")
def _run(args):
        url = args.get("url")
        if not url:
                raise ValueError("missing url")
        try:
                import httpx
        except ImportError as e:  # pragma: no cover - import guarded
                raise RuntimeError("httpx extra is not installed") from e
        r = httpx.get(url, timeout=15)
        r.raise_for_status()
        return {"text": r.text[:10000]}

spec = ToolSpec(name="web_fetch", input_model=None, run=_run)
