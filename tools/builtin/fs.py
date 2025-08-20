"""Filesystem write utility with policy enforcement."""
from __future__ import annotations

import difflib
import time
from pathlib import Path
from typing import Dict

from agent_mono import logger, policy
from agent_mono.fs_utils import write_text_atomic


def fs_write_text(path: Path, content: str, timeout: float = 10.0) -> Dict:
    start = time.time()
    try:
        policy.check("fs.write", path=path, source="tools.builtin.fs_write_text")
        original = path.read_text(encoding="utf-8") if path.exists() else ""
        write_text_atomic(path, content)
        if len(original) + len(content) <= 131072:
            diff = "\n".join(
                difflib.unified_diff(
                    original.splitlines(), content.splitlines(), lineterm=""
                )
            )
        else:
            diff = "<diff suppressed>"
        success, code, stderr = True, 0, ""
    except PermissionError:
        raise
    except Exception as e:  # pragma: no cover - unexpected errors
        success, code, stderr, diff = False, 1, str(e), ""
    duration_ms = int((time.time() - start) * 1000)
    bytes_written = len(content.encode("utf-8"))
    logger.log_event("tool.fs.write", success=success, duration_ms=duration_ms, bytes=bytes_written)
    return {
        "success": success,
        "code": code,
        "stdout": "",
        "stderr": stderr,
        "duration_ms": duration_ms,
        "meta": {
            "capability": "fs.write",
            "timeout_s": timeout,
            "path": str(path.expanduser().resolve()),
            "bytes": bytes_written,
        },
        "diff": diff,
    }
