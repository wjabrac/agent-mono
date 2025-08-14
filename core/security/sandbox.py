import multiprocessing as mp
from typing import Any, Callable, Dict


def _runner(fn: Callable[[Dict[str, Any]], Any], args: Dict[str, Any], out_q: mp.Queue) -> None:
    try:
        res = fn(args)
        out_q.put((True, res))
    except Exception as e:
        out_q.put((False, (type(e).__name__, str(e))))


def run_in_sandbox(fn: Callable[[Dict[str, Any]], Any], args: Dict[str, Any], timeout_s: int = 20) -> Any:
    out_q: mp.Queue = mp.Queue()
    p = mp.Process(target=_runner, args=(fn, args, out_q))
    p.daemon = True
    p.start()
    p.join(timeout_s)
    if p.is_alive():
        p.terminate(); p.join(1)
        raise TimeoutError("sandbox_timeout")
    ok, payload = out_q.get() if not out_q.empty() else (False, ("no_result", ""))
    if ok:
        return payload
    typ, msg = payload
    raise RuntimeError(f"sandbox_error:{typ}:{msg}")