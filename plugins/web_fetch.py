import json
try:
	import requests
except Exception:
	requests = None  # type: ignore
from core.tools.registry import ToolSpec
from core.instrumentation import instrument_tool


@instrument_tool("web_fetch")
def _run(args):
	url = args.get("url")
	if not url:
		raise ValueError("missing url")
	if requests is None:
		import urllib.request
		with urllib.request.urlopen(url, timeout=15) as r:  # type: ignore
			data = r.read()
			text = data.decode("utf-8", errors="ignore")
			return {"text": text[:10000]}
	r = requests.get(url, timeout=15)
	r.raise_for_status()
	return {"text": r.text[:10000]}

spec = ToolSpec(name="web_fetch", input_model=None, run=_run)
