import os
import sqlite3
import time
import threading
from typing import Optional

_DB_PATH = os.path.expanduser(os.getenv("AGENT_USAGE_DB", "~/.agent/usage.db"))
_lock = threading.Lock()

def _ensure_db() -> None:
    os.makedirs(os.path.dirname(_DB_PATH), exist_ok=True)
    with sqlite3.connect(_DB_PATH) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ts INTEGER,
                command TEXT,
                exit_code INTEGER,
                exec_ms INTEGER,
                error TEXT
            )
            """
        )
        conn.commit()

def log_run(command: str, exit_code: int, exec_ms: int, error: Optional[str] = None) -> None:
    _ensure_db()
    with _lock:
        with sqlite3.connect(_DB_PATH) as conn:
            conn.execute(
                "INSERT INTO runs (ts, command, exit_code, exec_ms, error) VALUES (?,?,?,?,?)",
                (int(time.time()), command, exit_code, exec_ms, error),
            )
            conn.commit()
