"""Shell helpers.

No operating-system sandbox is provided; commands run with the current
process privileges.
"""

from __future__ import annotations

import os
import subprocess
import time
from typing import Any, Dict


def run_shell(argv: list[str], timeout: float = 10.0) -> Dict[str, Any]:
    start = time.time()
    env = {**os.environ, "LC_ALL": "C.UTF-8"}
    proc = subprocess.run(
        argv,
        capture_output=True,
        text=True,
        timeout=timeout,
        env=env,
    )
    duration_ms = int((time.time() - start) * 1000)
    return {
        "success": proc.returncode == 0,
        "code": proc.returncode,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
        "duration_ms": duration_ms,
    }
