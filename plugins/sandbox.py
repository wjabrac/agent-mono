"""Utility wrapper for executing functions inside a sandbox.

POSIX platforms enforce isolation by default. On non-POSIX systems the sandbox
is unavailable unless an explicit unsafe mode is enabled via the
``ALLOW_UNSAFE_SANDBOX`` environment variable or ``allow_unsafe=True``. When
unsafe mode is used, a warning is printed to stderr and the function executes
without isolation.
"""
from __future__ import annotations

import os
import sys
from core.security.sandbox import SandboxTimeout, run_in_sandbox as _run_in_sandbox


def run_in_sandbox(fn):
    """Return a callable that executes ``fn`` within the sandbox."""
    def wrapper(args: dict, *, timeout_s: int = 20, allow_unsafe: bool = False):
        unsafe = allow_unsafe or os.getenv("ALLOW_UNSAFE_SANDBOX")
        if unsafe and os.name != "posix":
            print("WARNING: running without sandbox isolation", file=sys.stderr)
        return _run_in_sandbox(fn, args, timeout_s=timeout_s, allow_unsafe=allow_unsafe)
    return wrapper


__all__ = ["run_in_sandbox", "SandboxTimeout"]
