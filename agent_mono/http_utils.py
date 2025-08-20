"""HTTP helpers with size and content-type validation."""

from __future__ import annotations

import os
from urllib.request import Request, urlopen

_DEFAULT_TYPES = [
    "application/json",
    "application/xml",
    "text/",
]


def _allowed_types() -> list[str]:
    env = os.environ.get("HTTP_ALLOWED_CONTENT_TYPES")
    if env:
        return [t.strip() for t in env.split(",") if t.strip()]
    return _DEFAULT_TYPES


def fetch_text(
    url: str,
    timeout: float = 10.0,
    max_bytes: int = 1_000_000,
    allowed_types: list[str] | None = None,
) -> tuple[str, str]:
    types = allowed_types or _allowed_types()
    req = Request(url, headers={"User-Agent": "agent-mono"})
    with urlopen(req, timeout=timeout) as resp:
        ct = resp.headers.get("Content-Type", "")
        ct_main = ct.split(";")[0]
        if not any(
            (t.endswith("/") and ct_main.startswith(t))
            or (t.endswith("+json") and ct_main.startswith("application/") and ct_main.endswith("+json"))
            or ct_main == t
            for t in types
        ):
            raise ValueError(f"unexpected content-type {ct!r}")
        data = resp.read(max_bytes + 1)
        if len(data) > max_bytes:
            raise ValueError("response too large")
        encoding = resp.headers.get_content_charset("utf-8")
        return data.decode(encoding, errors="strict"), encoding
