diff --git a/core/memory/db.py b/core/memory/db.py
index 1111111..2222222 100644
--- a/core/memory/db.py
+++ b/core/memory/db.py
@@ -1,3 +1,4 @@
-import os, sqlite3, time, uuid
+import os
+import sqlite3
+import time
+import uuid
@@
 DB_PATH = os.getenv("AGENT_DB", "data/agent_memory.sqlite")
 MEM_DDL = [
@@
-<<<<<<< codex/add-advanced-agent-behaviors-and-rag-capabilities-90zrt3
-"""CREATE TABLE IF NOT EXISTS memory_messages(
+    """CREATE TABLE IF NOT EXISTS memory_messages(
   id TEXT PRIMARY KEY,
   thread_id TEXT,
   sender TEXT,
   recipient TEXT,
   content TEXT,
   created_at INTEGER DEFAULT (strftime('%s','now'))
 );""",
-# new cache table
-"""CREATE TABLE IF NOT EXISTS tool_cache(
-=======
-    # new cache table
-    """CREATE TABLE IF NOT EXISTS tool_cache(
->>>>>>> main
+    # new cache table
+    """CREATE TABLE IF NOT EXISTS tool_cache(
   cache_key TEXT PRIMARY KEY,
   tool TEXT NOT NULL,
   args_hash TEXT NOT NULL,
@@
 def get_conn():
     conn = sqlite3.connect(DB_PATH)
     conn.execute("PRAGMA journal_mode=WAL;")
     return conn
@@
 def init():
     with get_conn() as c:
         for ddl in MEM_DDL:
             c.execute(ddl)
@@
-def kv_recent(thread_id: str | None, limit: int = 20) -> list[tuple[str, str, int]]:
-<<<<<<< codex/add-advanced-agent-behaviors-and-rag-capabilities-90zrt3
-	if not thread_id:
-		return []
-	with get_conn() as c:
-		rows = c.execute(
-			"SELECT key, value, created_at FROM session_kv WHERE thread_id=? ORDER BY created_at DESC LIMIT ?",
-			(thread_id, limit)
-                ).fetchall()
-	return [(r[0], r[1], int(r[2])) for r in rows]
+def kv_recent(thread_id: str | None, limit: int = 20) -> list[tuple[str, str, int]]:
+    if not thread_id:
+        return []
+    with get_conn() as c:
+        rows = c.execute(
+            "SELECT key, value, created_at FROM session_kv WHERE thread_id=? ORDER BY created_at DESC LIMIT ?",
+            (thread_id, limit),
+        ).fetchall()
+    return [(r[0], r[1], int(r[2])) for r in rows]
@@
-# Simple messaging helpers
-
-def save_message(thread_id: str, sender: str, recipient: str, content: str) -> None:
-	with get_conn() as c:
-		c.execute(
-			"INSERT INTO memory_messages(id, thread_id, sender, recipient, content) VALUES(?,?,?,?,?)",
-			(uuid.uuid4().hex, thread_id, sender, recipient, content),
-		)
-
-
-def fetch_messages(thread_id: str, recipient: str) -> list[dict[str, str | int]]:
-	with get_conn() as c:
-		rows = c.execute(
-			"SELECT id, sender, recipient, content, created_at FROM memory_messages WHERE thread_id=? AND recipient=? ORDER BY created_at",
-			(thread_id, recipient),
-		).fetchall()
-	return [
-		{
-			"id": r[0],
-			"sender": r[1],
-			"recipient": r[2],
-			"content": r[3],
-			"created_at": int(r[4]),
-		}
-		for r in rows
-	]
+# Simple messaging helpers
+def save_message(thread_id: str, sender: str, recipient: str, content: str) -> None:
+    with get_conn() as c:
+        c.execute(
+            "INSERT INTO memory_messages(id, thread_id, sender, recipient, content) VALUES(?,?,?,?,?)",
+            (uuid.uuid4().hex, thread_id, sender, recipient, content),
+        )
+
+
+def fetch_messages(thread_id: str, recipient: str) -> list[dict[str, str | int]]:
+    with get_conn() as c:
+        rows = c.execute(
+            "SELECT id, sender, recipient, content, created_at "
+            "FROM memory_messages WHERE thread_id=? AND recipient=? ORDER BY created_at",
+            (thread_id, recipient),
+        ).fetchall()
+    return [
+        {
+            "id": r[0],
+            "sender": r[1],
+            "recipient": r[2],
+            "content": r[3],
+            "created_at": int(r[4]),
+        }
+        for r in rows
+    ]

