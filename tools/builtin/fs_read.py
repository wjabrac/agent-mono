"""Filesystem read utility with policy enforcement."""
from __future__ import annotations

import time
from pathlib import Path
from typing import Dict

from agent_mono import logger, policy


def fs_read(path: Path, timeout: float = 10.0) -> Dict:
    start = time.time()
    try:
        policy.check("fs.read", path=path, source="tools.builtin.fs_read")
        content = path.read_text(encoding="utf-8")
        success, code, stderr = True, 0, ""
    except PermissionError:
        raise
    except Exception as e:  # pragma: no cover - unexpected errors
        success, code, stderr, content = False, 1, str(e), ""
    duration_ms = int((time.time() - start) * 1000)
    bytes_read = len(content.encode("utf-8"))
    logger.log_event("tool.fs.read", success=success, duration_ms=duration_ms, bytes=bytes_read)
    return {
        "success": success,
        "code": code,
        "stdout": content,
        "stderr": stderr,
        "duration_ms": duration_ms,
        "meta": {
            "capability": "fs.read",
            "timeout_s": timeout,
            "path": str(path.expanduser().resolve()),
            "bytes": bytes_read,
        },
    }
