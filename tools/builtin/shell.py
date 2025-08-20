"""Shell execution utility with policy enforcement."""
from __future__ import annotations

from typing import Dict, List

from agent_mono import logger, policy
from agent_mono.shell_utils import run_shell


def shell_run_sandboxed(argv: List[str], timeout: float = 10.0) -> Dict:
    try:
        policy.check(
            "subprocess", source="tools.builtin.shell_run_sandboxed"
        )
        result = run_shell(argv, timeout=timeout)
    except PermissionError:
        raise
    except Exception as e:  # pragma: no cover - unexpected errors
        result = {
            "success": False,
            "code": 1,
            "stdout": "",
            "stderr": str(e),
            "duration_ms": 0,
        }
    logger.log_event(
        "tool.subprocess",
        success=result["success"],
        duration_ms=result["duration_ms"],
        bytes=len(result.get("stdout", "").encode()) + len(result.get("stderr", "").encode()),
    )
    result["meta"] = {
        "capability": "subprocess",
        "timeout_s": timeout,
        "argv": argv,
    }
    return result
