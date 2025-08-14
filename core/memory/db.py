import os, sqlite3, time, uuid
DB_PATH = os.getenv("AGENT_DB", "data/agent_memory.sqlite")
MEM_DDL = [
"""CREATE TABLE IF NOT EXISTS memory_entities(
  id TEXT PRIMARY KEY, name TEXT NOT NULL, type TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);""",
"""CREATE TABLE IF NOT EXISTS memory_claims(
  id TEXT PRIMARY KEY, entity_id TEXT, predicate TEXT,
  value TEXT, value_type TEXT, source_content_id TEXT,
  chunk_id TEXT, span_start INTEGER, span_end INTEGER,
  trust REAL DEFAULT 0.5, tags TEXT DEFAULT '[]',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY(entity_id) REFERENCES memory_entities(id));""",
"""CREATE TABLE IF NOT EXISTS memory_facts(
  id TEXT PRIMARY KEY, claim_id TEXT NOT NULL, status TEXT DEFAULT 'active',
  version INTEGER DEFAULT 1, notes TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY(claim_id) REFERENCES memory_claims(id));""",
"""CREATE TABLE IF NOT EXISTS memory_threads(
  id TEXT PRIMARY KEY, title TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);""",
"""CREATE TABLE IF NOT EXISTS memory_pins(
  id TEXT PRIMARY KEY, owner_type TEXT, owner_id TEXT, note TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);""",
"""CREATE TABLE IF NOT EXISTS traces(
  id TEXT PRIMARY KEY, thread_id TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);""",
"""CREATE TABLE IF NOT EXISTS trace_events(
  id TEXT PRIMARY KEY, trace_id TEXT, phase TEXT, role TEXT, payload TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY(trace_id) REFERENCES traces(id));""",
"""CREATE TABLE IF NOT EXISTS memory_messages(
  id TEXT PRIMARY KEY,
  thread_id TEXT,
  sender TEXT,
  recipient TEXT,
  content TEXT,
  created_at INTEGER DEFAULT (strftime('%s','now'))
);""",
# new cache table
"""CREATE TABLE IF NOT EXISTS tool_cache(
  cache_key TEXT PRIMARY KEY,
  tool TEXT NOT NULL,
  args_hash TEXT NOT NULL,
  value TEXT,
  version INTEGER DEFAULT 1,
  ttl_s INTEGER DEFAULT 0,
  created_at INTEGER DEFAULT (strftime('%s','now'))
);""",
# session key-value store
"""CREATE TABLE IF NOT EXISTS session_kv(
  id TEXT PRIMARY KEY,
  thread_id TEXT,
  key TEXT,
  value TEXT,
  created_at INTEGER DEFAULT (strftime('%s','now'))
);""",
"""CREATE TABLE IF NOT EXISTS rate_counters(
  key TEXT PRIMARY KEY,
  count INTEGER DEFAULT 0,
  window_start INTEGER DEFAULT 0
);""",
]

def get_conn():
	conn = sqlite3.connect(DB_PATH)
	conn.execute("PRAGMA journal_mode=WAL;")
	return conn

def init():
	with get_conn() as c:
		for ddl in MEM_DDL:
			c.execute(ddl)

# Simple cache helpers

def cache_get(tool: str, args_hash: str) -> str | None:
	with get_conn() as c:
		row = c.execute(
			"SELECT value, ttl_s, created_at FROM tool_cache WHERE tool=? AND args_hash=?",
			(tool, args_hash)
		).fetchone()
	if not row:
		return None
	value, ttl_s, created_at = row
	if ttl_s and int(time.time()) - int(created_at) > int(ttl_s):
		with get_conn() as c:
			c.execute("DELETE FROM tool_cache WHERE tool=? AND args_hash=?", (tool, args_hash))
		return None
	return value

def cache_put(tool: str, args_hash: str, value: str, ttl_s: int = 0, version: int = 1) -> None:
	with get_conn() as c:
		c.execute(
			"INSERT OR REPLACE INTO tool_cache(cache_key, tool, args_hash, value, version, ttl_s, created_at) VALUES(?,?,?,?,?,?,strftime('%s','now'))",
			(f"{tool}:{args_hash}", tool, args_hash, value, version, ttl_s)
		)

# Session KV helpers

def kv_put(thread_id: str | None, key: str, value: str) -> None:
	if not thread_id:
		return
	with get_conn() as c:
		c.execute(
			"INSERT OR REPLACE INTO session_kv(id, thread_id, key, value, created_at) VALUES(?,?,?,?,strftime('%s','now'))",
			(f"{thread_id}:{key}", thread_id, key, value)
		)

def kv_get(thread_id: str | None, key: str) -> str | None:
	if not thread_id:
		return None
	with get_conn() as c:
		row = c.execute("SELECT value FROM session_kv WHERE thread_id=? AND key=?", (thread_id, key)).fetchone()
	return row[0] if row else None

def kv_recent(thread_id: str | None, limit: int = 20) -> list[tuple[str, str, int]]:
	if not thread_id:
		return []
	with get_conn() as c:
		rows = c.execute(
			"SELECT key, value, created_at FROM session_kv WHERE thread_id=? ORDER BY created_at DESC LIMIT ?",
			(thread_id, limit)
                ).fetchall()
	return [(r[0], r[1], int(r[2])) for r in rows]


# Simple messaging helpers

def save_message(thread_id: str, sender: str, recipient: str, content: str) -> None:
	with get_conn() as c:
		c.execute(
			"INSERT INTO memory_messages(id, thread_id, sender, recipient, content) VALUES(?,?,?,?,?)",
			(uuid.uuid4().hex, thread_id, sender, recipient, content),
		)


def fetch_messages(thread_id: str, recipient: str) -> list[dict[str, str | int]]:
	with get_conn() as c:
		rows = c.execute(
			"SELECT id, sender, recipient, content, created_at FROM memory_messages WHERE thread_id=? AND recipient=? ORDER BY created_at",
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

