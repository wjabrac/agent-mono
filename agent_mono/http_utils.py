from urllib.request import Request, urlopen


def fetch_text(url: str, timeout: float = 10.0, max_bytes: int = 1_000_000) -> str:
    req = Request(url, headers={"User-Agent": "agent-mono"})
    with urlopen(req, timeout=timeout) as resp:
        ct = resp.headers.get("Content-Type", "")
        data = resp.read(max_bytes + 1)
        if len(data) > max_bytes:
            raise ValueError("response too large")
        if "text" not in ct and "json" not in ct:
            raise ValueError(f"unexpected content-type {ct!r}")
        return data.decode("utf-8", errors="strict")
