from __future__ import annotations

import json
import sqlite3
import time
from pathlib import Path
from hashlib import sha256
from typing import Optional

DB_PATH = Path("data/safety_audit.sqlite")
DB_PATH.parent.mkdir(exist_ok=True)

_conn = sqlite3.connect(DB_PATH)
_conn.execute(
    """
    CREATE TABLE IF NOT EXISTS audit_events(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ts REAL,
        actor TEXT,
        plugin TEXT,
        command TEXT,
        decision TEXT,
        rate_limited INTEGER,
        error_type TEXT,
        error_msg TEXT,
        args_hash TEXT,
        sandbox_path TEXT
    )
    """
)
_conn.execute(
    """
    CREATE TABLE IF NOT EXISTS rate_counters(
        key TEXT PRIMARY KEY,
        window_start_ts REAL,
        count INTEGER
    )
    """
)
_conn.commit()


def _hash_args(args: dict) -> str:
    data = json.dumps(args, sort_keys=True)
    return sha256(data.encode()).hexdigest()


def record(decision: str, actor: str, plugin: str, command: str, args: dict,
           sandbox_path: Optional[str], rate_limited: bool = False,
           error: Optional[BaseException] = None) -> None:
    error_type = type(error).__name__ if error else None
    error_msg = str(error) if error else None
    _conn.execute(
        "INSERT INTO audit_events(ts, actor, plugin, command, decision, rate_limited, error_type, error_msg, args_hash, sandbox_path)"
        " VALUES(?,?,?,?,?,?,?,?,?,?)",
        (
            time.time(),
            actor,
            plugin,
            command,
            decision,
            int(rate_limited),
            error_type,
            error_msg,
            _hash_args(args),
            sandbox_path,
        ),
    )
    _conn.commit()


def rate_check(plugin: str, command: str, actor: str, limit: int) -> bool:
    key = f"{actor}:{plugin}:{command}"
    now = time.time()
    cur = _conn.execute(
        "SELECT window_start_ts, count FROM rate_counters WHERE key=?", (key,)
    )
    row = cur.fetchone()
    if row and now - row[0] < 60:
        if row[1] >= limit:
            return True
        _conn.execute(
            "UPDATE rate_counters SET count=count+1 WHERE key=?", (key,)
        )
    else:
        _conn.execute(
            "REPLACE INTO rate_counters(key, window_start_ts, count) VALUES (?,?,1)",
            (key, now),
        )
    _conn.commit()
    return False
