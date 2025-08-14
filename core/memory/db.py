import os
import sqlite3
import time
import uuid
from typing import List, Tuple, Dict, Optional

# Backward-compat: preserve DB_PATH while centralizing via _db_path()
DB_PATH = os.getenv("AGENT_DB", "data/agent_memory.sqlite")

def _db_path() -> str:
    return os.getenv("AGENT_DB", DB_PATH)

MEM_DDL = [
    """CREATE TABLE IF NOT EXISTS memory_messages(
   id TEXT PRIMARY KEY,
   thread_id TEXT,
   sender TEXT,
   recipient TEXT,
   content TEXT,
   created_at INTEGER DEFAULT (strftime('%s','now'))
 );""",
    """CREATE TABLE IF NOT EXISTS tool_cache(
   cache_key TEXT PRIMARY KEY,
   tool TEXT NOT NULL,
   args_hash TEXT NOT NULL,
   result TEXT,
   created_at INTEGER DEFAULT (strftime('%s','now'))
 );""",
    """CREATE TABLE IF NOT EXISTS session_kv(
   thread_id TEXT,
   key TEXT,
   value TEXT,
   created_at INTEGER DEFAULT (strftime('%s','now')),
   PRIMARY KEY (thread_id, key)
);""",
    """CREATE TABLE IF NOT EXISTS memory_threads(
   id TEXT PRIMARY KEY,
   title TEXT,
   created_at INTEGER DEFAULT (strftime('%s','now'))
 );""",
    """CREATE TABLE IF NOT EXISTS traces(
   id TEXT PRIMARY KEY,
   thread_id TEXT,
   created_at INTEGER DEFAULT (strftime('%s','now'))
 );""",
    """CREATE TABLE IF NOT EXISTS trace_events(
   id TEXT PRIMARY KEY,
   trace_id TEXT NOT NULL,
   phase TEXT,
   role TEXT,
   payload TEXT,
   created_at INTEGER DEFAULT (strftime('%s','now'))
 );""",
]

def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(_db_path())
    conn.execute("PRAGMA journal_mode=WAL;")
    return conn

def init() -> None:
    with get_conn() as c:
        for ddl in MEM_DDL:
            c.execute(ddl)

def cache_put(tool: str, args_hash: str, result: str) -> None:
    key = f"{tool}:{args_hash}"
    with get_conn() as c:
        c.execute(
            "INSERT OR REPLACE INTO tool_cache(cache_key, tool, args_hash, result, created_at) "
            "VALUES(?,?,?,?,?)",
            (key, tool, args_hash, result, int(time.time())),
        )

def cache_get(tool: str, args_hash: str) -> Optional[str]:
    key = f"{tool}:{args_hash}"
    with get_conn() as c:
        row = c.execute(
            "SELECT result FROM tool_cache WHERE cache_key=?",
            (key,),
        ).fetchone()
    return row[0] if row else None

def kv_put(thread_id: str, key: str, value: str) -> None:
    with get_conn() as c:
        c.execute(
            "INSERT OR REPLACE INTO session_kv(thread_id, key, value, created_at) "
            "VALUES(?,?,?,?)",
            (thread_id, key, value, int(time.time())),
        )

def kv_recent(thread_id: Optional[str], limit: int = 20) -> List[Tuple[str, str, int]]:
    if not thread_id:
        return []
    with get_conn() as c:
        rows = c.execute(
            "SELECT key, value, created_at FROM session_kv "
            "WHERE thread_id=? ORDER BY created_at DESC LIMIT ?",
            (thread_id, limit),
        ).fetchall()
    return [(r[0], r[1], int(r[2])) for r in rows]

# Simple messaging helpers

def save_message(thread_id: str, sender: str, recipient: str, content: str) -> None:
    with get_conn() as c:
        c.execute(
            "INSERT INTO memory_messages(id, thread_id, sender, recipient, content) VALUES(?,?,?,?,?)",
            (uuid.uuid4().hex, thread_id, sender, recipient, content),
        )

def fetch_messages(thread_id: str, recipient: str) -> List[Dict[str, str | int]]:
    with get_conn() as c:
        rows = c.execute(
            "SELECT id, sender, recipient, content, created_at "
            "FROM memory_messages WHERE thread_id=? AND recipient=? ORDER BY created_at",
            (thread_id, recipient),
        ).fetchall()
    return [
        {
            "id": r[0],
            "sender": r[1],
            "recipient": r[2],
            "content": r[3],
            "created_at": int(r[4]),
        }
        for r in rows
    ]
