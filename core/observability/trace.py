import json, uuid
from typing import Optional, Dict, Any, List
from core.memory.db import get_conn, init as init_db
init_db()

def open_thread(title: str="") -> str:
		id = uuid.uuid4().hex
		c = get_conn(); c.execute("INSERT INTO memory_threads(id,title) VALUES(?,?)",(id,title))
		c.commit(); c.close(); return id

def start_trace(thread_id: Optional[str]=None) -> str:
	tr = uuid.uuid4().hex
	c = get_conn(); c.execute("INSERT INTO traces(id,thread_id) VALUES(?,?)",(tr,thread_id))
	c.commit(); c.close(); return tr

def log_event(trace_id: str, phase: str, role: str, payload: Dict[str,Any]) -> str:
	eid = uuid.uuid4().hex
	c = get_conn(); c.execute(
	  "INSERT INTO trace_events(id,trace_id,phase,role,payload) VALUES(?,?,?,?,?)",
	  (eid, trace_id, phase, role, json.dumps(payload, ensure_ascii=False)))
	c.commit(); c.close(); return eid

# Lightweight summary for local telemetry consumers

def get_trace_summary(trace_id: str) -> List[Dict[str, Any]]:
	c = get_conn()
	rows = c.execute("SELECT phase, role, payload, created_at FROM trace_events WHERE trace_id=? ORDER BY created_at ASC", (trace_id,)).fetchall()
	c.close()
	out: List[Dict[str, Any]] = []
	for phase, role, payload, created_at in rows:
		try:
			data = json.loads(payload)
		except Exception:
			data = {"raw": payload}
		out.append({"phase": phase, "role": role, "payload": data, "ts": created_at})
	return out
