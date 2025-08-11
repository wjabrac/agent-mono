import os, sqlite3
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
]
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL;")
    return conn
def init():
    c = get_conn()
    for ddl in MEM_DDL: c.execute(ddl)
    c.commit(); c.close()
