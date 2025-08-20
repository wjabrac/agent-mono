from __future__ import annotations

import multiprocessing as mp
import resource
from typing import Any, Callable, Dict


def _run_target(fn: Callable[[Dict[str, Any]], Dict[str, Any]], args: Dict[str, Any], q: mp.Queue) -> None:
    try:
        try:
            resource.setrlimit(resource.RLIMIT_CPU, (2, 2))
            resource.setrlimit(resource.RLIMIT_AS, (256 * 1024 * 1024, 256 * 1024 * 1024))
        except Exception:
            pass
        result = fn(args)
        q.put((True, result))
    except Exception as e:  # pragma: no cover - sandbox safety
        q.put((False, f"{type(e).__name__}: {e}"))


def run_in_sandbox(fn: Callable[[Dict[str, Any]], Dict[str, Any]]) -> Callable[[Dict[str, Any]], Dict[str, Any]]:
    """Execute a function in a separate process with basic resource limits."""

    def wrapper(args: Dict[str, Any]) -> Dict[str, Any]:
        q: mp.Queue = mp.Queue()
        p = mp.Process(target=_run_target, args=(fn, args, q))
        p.start()
        p.join()
        ok, payload = q.get()
        if not ok:
            raise RuntimeError(payload)
        return payload

    return wrapper
