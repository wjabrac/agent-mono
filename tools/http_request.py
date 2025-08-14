from pydantic import BaseModel
from core.tools.microtool import microtool

try:
	httpx = __import__("httpx")
except Exception:
	httpx = None
try:
	requests = __import__("requests")
except Exception:
	requests = None


class HttpInput(BaseModel):
	url: str
	method: str = "GET"
	headers: dict | None = None
	params: dict | None = None
	json: dict | None = None
	data: dict | None = None
	timeout_s: int = 20
	parse_json: bool = True


@microtool("http_request", description="Generic HTTP request primitive (GET/POST/etc)", tags=["http","network","request"], input_model=HttpInput)
def http_request(url, method="GET", headers=None, params=None, json=None, data=None, timeout_s=20, parse_json=True) -> dict:
	if httpx is not None:
		with httpx.Client(timeout=timeout_s) as c:
			r = c.request(method, url, headers=headers, params=params, json=json, data=data)
			r.raise_for_status()
			return {"status": r.status_code, "headers": dict(r.headers), "json": r.json()} if parse_json else {"status": r.status_code, "headers": dict(r.headers), "text": r.text}
	elif requests is not None:
		r = requests.request(method, url, headers=headers, params=params, json=json, data=data, timeout=timeout_s)
		r.raise_for_status()
		return {"status": r.status_code, "headers": dict(r.headers), "json": r.json()} if parse_json else {"status": r.status_code, "headers": dict(r.headers), "text": r.text}
	else:
		raise RuntimeError("no_http_client_available")