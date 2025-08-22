from __future__ import annotations

import importlib
import multiprocessing as mp
import os
from queue import Empty
from typing import Any, Callable, Dict, Tuple


class SandboxTimeout(TimeoutError):
    """Raised when the sandboxed function exceeds its time limit."""


def _resolve_qualname(mod, qualname: str):
    obj = mod
    for part in qualname.split("."):
        obj = getattr(obj, part)
    return obj


def _runner(fn_ref: Tuple[str, str], args: Dict[str, Any], out_q: mp.Queue) -> None:
    mod_name, qualname = fn_ref
    try:
        mod = importlib.import_module(mod_name)
        fn = _resolve_qualname(mod, qualname)
        res = fn(args)
        out_q.put((True, res))
    except Exception as e:  # pragma: no cover - defensive
        out_q.put((False, (type(e).__name__, str(e))))


def run_in_sandbox(
    fn: Callable[[Dict[str, Any]], Any],
    args: Dict[str, Any],
    timeout_s: int = 20,
    *,
    allow_unsafe: bool = False,
) -> Any:
    """Execute `fn` in a separate process with timeouts and platform checks."""
    unsafe = allow_unsafe or os.getenv("ALLOW_UNSAFE_SANDBOX")
    if unsafe:
        return fn(args)

    if os.name != "posix":
        raise RuntimeError("sandbox unsupported on this platform")

    out_q: mp.Queue = mp.Queue()
    fn_ref = (fn.__module__, fn.__qualname__)
    p = mp.Process(target=_runner, args=(fn_ref, args, out_q))
    p.daemon = True
    p.start()
    p.join(timeout_s)

    if p.is_alive():
        p.terminate()
        p.join(1)
        raise SandboxTimeout("sandbox timeout")

    try:
        ok, payload = out_q.get(timeout=1)
    except Empty:
        raise SandboxTimeout("no result")

    if ok:
        return payload

    typ, msg = payload
    raise RuntimeError(f"sandbox_error:{typ}:{msg}")
