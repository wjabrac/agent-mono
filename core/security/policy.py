import os, time, sqlite3
from typing import Dict, Any, Optional, Tuple

from core.memory.db import get_conn, init as init_db

# Feature flags (defaults captured at import, but helpers read env each call)
_POLICY_ENGINE_ENABLED = os.getenv("POLICY_ENGINE_ENABLED", "false").lower() in ("1","true","yes")
_HTTP_RATE_LIMIT_PER_MIN = int(os.getenv("HTTP_RATE_LIMIT_PER_MIN", "0") or 0)
_ALLOWED_TOOLS = {t.strip() for t in os.getenv("ALLOWED_TOOLS", "").split(",") if t.strip()}
_FS_SAFE_ROOTS = [p for p in os.getenv("FS_SAFE_ROOTS", "").split(",") if p]
_MAX_OUTPUT_BYTES = int(os.getenv("MAX_OUTPUT_BYTES", "0") or 0)


def _enabled() -> bool:
	return os.getenv("POLICY_ENGINE_ENABLED", str(_POLICY_ENGINE_ENABLED)).lower() in ("1","true","yes")

def _http_limit() -> int:
	try:
		return int(os.getenv("HTTP_RATE_LIMIT_PER_MIN", str(_HTTP_RATE_LIMIT_PER_MIN)) or 0)
	except Exception:
		return _HTTP_RATE_LIMIT_PER_MIN

def _allowed() -> set[str]:
	raw = os.getenv("ALLOWED_TOOLS", ",".join(sorted(_ALLOWED_TOOLS)))
	return {t.strip() for t in raw.split(",") if t.strip()}

def _safe_roots() -> list[str]:
	raw = os.getenv("FS_SAFE_ROOTS", ",".join(_FS_SAFE_ROOTS))
	return [p for p in raw.split(",") if p]

def _max_output() -> int:
	try:
		return int(os.getenv("MAX_OUTPUT_BYTES", str(_MAX_OUTPUT_BYTES)) or 0)
	except Exception:
		return _MAX_OUTPUT_BYTES

init_db()

# Local table for rate limiting counters (separate from trace tables to keep scope clear)
_DEF_DDL = [
    """CREATE TABLE IF NOT EXISTS rate_counters(
      key TEXT PRIMARY KEY,
      count INTEGER DEFAULT 0,
      window_start INTEGER
    );""",
]

def _init_rl_db():
    c = get_conn()
    for ddl in _DEF_DDL:
        c.execute(ddl)
    c.commit(); c.close()

_init_rl_db()


def _now_minute() -> int:
    return int(time.time() // 60)


def _inc_counter(key: str) -> Tuple[int, int]:
    c = get_conn()
    row = c.execute("SELECT count, window_start FROM rate_counters WHERE key= ?", (key,)).fetchone()
    now_win = _now_minute()
    if not row:
        c.execute("INSERT INTO rate_counters(key, count, window_start) VALUES(?,?,?)", (key, 1, now_win))
        c.commit(); c.close(); return 1, now_win
    count, win = row
    if win != now_win:
        count = 0; win = now_win
    count += 1
    c.execute("INSERT OR REPLACE INTO rate_counters(key, count, window_start) VALUES(?,?,?)", (key, count, win))
    c.commit(); c.close(); return count, win

# Basic tool metadata for decisions
RISKY_TOOLS = {t.strip() for t in os.getenv("RISKY_TOOLS", "mcp.shell.run").split(",") if t.strip()}


def is_tool_allowed(tool_name: str) -> bool:
    if not _enabled():
        return True
    allowed = _allowed()
    if allowed and tool_name not in allowed:
        return False
    return True


def enforce_path_restrictions(tool_name: str, args: Dict[str, Any]) -> None:
    if not _enabled():
        return
    roots = _safe_roots()
    if roots and any(k in args for k in ("path", "db_path", "repo")):
        path = args.get("path") or args.get("db_path") or args.get("repo")
        if not isinstance(path, str):
            return
        norm = os.path.abspath(path)
        ok = any(norm.startswith(os.path.abspath(root)) for root in roots)
        if not ok:
            raise PermissionError(f"path_restricted: {norm}")


def enforce_http_rate_limit(tool_name: str, args: Dict[str, Any]) -> None:
    if not _enabled():
        return
    limit = _http_limit()
    if limit <= 0:
        return
    if tool_name.startswith("mcp.http.") or tool_name.endswith("_fetch") or tool_name == "web_fetch":
        count, win = _inc_counter("http")
        if count > limit:
            raise RuntimeError("rate_limited:http_per_min")


def is_risky_tool(tool_name: str) -> bool:
    return tool_name in RISKY_TOOLS


def check_tool_allowed(tool_name: str, args: Dict[str, Any]) -> None:
    if not is_tool_allowed(tool_name):
        raise PermissionError(f"tool_not_allowed:{tool_name}")
    enforce_path_restrictions(tool_name, args)
    enforce_http_rate_limit(tool_name, args)


def enforce_output_limits(tool_name: str, output: Any) -> None:
    """Enforce simple output size limits if configured.

    If MAX_OUTPUT_BYTES > 0 and the serialized output exceeds the limit, raise.
    """
    if not _enabled():
        return
    lim = _max_output()
    if lim <= 0:
        return
    try:
        import json
        blob = json.dumps(output, ensure_ascii=False)
    except Exception:
        blob = str(output)
    if len(blob.encode("utf-8")) > lim:
        raise RuntimeError("output_too_large")