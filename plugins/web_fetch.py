from core.tools.registry import ToolSpec
from core.instrumentation import instrument_tool
from urllib.parse import urlsplit


@instrument_tool("web_fetch")
def _run(args):
    url = args.get("url")
    if not url:
        raise ValueError("missing url")
    parts = urlsplit(url)
    if parts.scheme not in {"http", "https"}:
        raise ValueError("unsupported URL scheme")
    try:
        import httpx  # type: ignore
    except ImportError as e:  # pragma: no cover
        raise RuntimeError("httpx extra is not installed; install with `.[http]`") from e
    # Tight but reasonable defaults; total read cap to 10000 chars
    timeout = httpx.Timeout(connect=5.0, read=5.0, write=5.0, pool=5.0)
    headers = {"User-Agent": "agent-mono/0.1 (+github.com/wjabrac/agent-mono)"}
    with httpx.Client(timeout=timeout, headers=headers, http2=False) as client:
        r = client.get(url, follow_redirects=True)
        r.raise_for_status()
        return {"text": r.text[:10000]}


spec = ToolSpec(name="web_fetch", input_model=None, run=_run)

