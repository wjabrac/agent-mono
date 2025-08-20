"""HTTP fetch utility with policy enforcement."""
from __future__ import annotations

import time
from typing import Dict

from agent_mono import logger, policy
from agent_mono.http_utils import fetch_text


def http_fetch_text(
    url: str,
    timeout: float = 10.0,
    max_bytes: int = 1_000_000,
) -> Dict:
    start = time.time()
    try:
        policy.check("network", source="tools.builtin.http_fetch_text")
        text, encoding = fetch_text(url, timeout=timeout, max_bytes=max_bytes)
        success, code, stderr = True, 0, ""
    except PermissionError:
        raise
    except Exception as e:  # pragma: no cover - unexpected errors
        success, code, stderr, text, encoding = False, 1, str(e), "", ""
    duration_ms = int((time.time() - start) * 1000)
    bytes_read = len(text.encode(encoding or "utf-8"))
    logger.log_event("tool.http", success=success, duration_ms=duration_ms, bytes=bytes_read)
    return {
        "success": success,
        "code": code,
        "stdout": text,
        "stderr": stderr,
        "duration_ms": duration_ms,
        "meta": {
            "capability": "network",
            "timeout_s": timeout,
            "url": url,
            "bytes": bytes_read,
            "encoding": encoding,
            "max_bytes": max_bytes,
        },
    }
