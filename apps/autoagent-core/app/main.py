from fastapi import FastAPI, Query
from pydantic import BaseModel
from typing import List, Dict, Any
import os
from core.agentControl import execute_steps, plan_steps
from core.observability.insights import compute_insights
from core.observability.trace import list_recent_traces, get_trace_summary
try:
	from core.knowledge.search import semantic_query  # type: ignore
except Exception:
	def semantic_query(q: str, top_k: int = 5): return []
app = FastAPI(title="autoagent-core")
class StepModel(BaseModel):
	tool: str
	args: Dict[str, Any]
	depends_on: List[str] | None = None
	ttl_s: int = 0
	fallback_tool: str | None = None
	timeout_s: int = 20
	retries: int = 1
class RunModel(BaseModel):
	prompt: str
	steps: List[StepModel] | None = None
@app.get("/health")
def health():
	return {"ok": True}
@app.get("/insights")
def insights():
	return compute_insights()
@app.get("/tools")
def list_tools():
	from core.tools.registry import _REGISTRY  # type: ignore
	return sorted(list(_REGISTRY.keys()))
@app.post("/plan")
def plan(body: Dict[str, Any]):
    prompt = body.get("prompt", "")
    return {"steps": plan_steps(prompt)}

@app.post("/approve")
def approve():
    # replace flag-file based approval; create token so HITL gate lifts
    token = os.getenv("HITL_TOKEN", "/run/hitl.ok")
    path = token if os.path.isabs(token) else os.path.join(os.getenv("LOCAL_ROOT","."), token)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write("ok")
    return {"ok": True}
@app.post("/run")
def run_agent(req: RunModel, thread: str | None = Query(default=None), tags: List[str] | None = Query(default=None)):
	steps = None if req.steps is None else [s.dict() for s in req.steps]
	return execute_steps(req.prompt, steps, thread_id=thread, tags=tags or [])
# Optional: async via Temporal if worker is up and TEMPORAL_HOST is set
try:
	from temporalio.client import Client
	HAVE_TEMPORAL = True
except Exception:
	HAVE_TEMPORAL = False
@app.post("/run_async")
async def run_async(req: RunModel, thread: str | None = Query(default=None), tags: List[str] | None = Query(default=None)):
	if not HAVE_TEMPORAL:
		return {"error": "Temporal client not available in app container"}
	target = os.getenv("TEMPORAL_HOST","temporal:7233")
	client = await Client.connect(target)
	wid = f"agent-{thread or 'default'}"
	steps = None if req.steps is None else [s.dict() for s in req.steps]
	# Start by workflow name to avoid importing worker module
	handle = await client.start_workflow(
		"AgentWorkflow",
		req.prompt,
		steps,
		thread,
		tags or [],
		id=wid,
		task_queue="agent-tq",
	)
	return {"workflow_id": handle.id, "run_id": handle.run_id}

# Observability: traces and semantic search
@app.get("/traces")
def traces(limit: int = 50):
	return list_recent_traces(limit=limit)

@app.get("/traces/{trace_id}")
def trace_detail(trace_id: str):
	return {"trace_id": trace_id, "events": get_trace_summary(trace_id)}

@app.get("/search")
def search(q: str, k: int = 5):
	return {"results": semantic_query(q, top_k=k)}

# Task templates (in-memory JSON file under data/templates.json)
_TPL_PATH = os.getenv("TEMPLATES_PATH", "data/templates.json")

def _load_tpl():
	os.makedirs(os.path.dirname(_TPL_PATH) or ".", exist_ok=True)
	if not os.path.exists(_TPL_PATH):
		return {}
	import json
	try:
		with open(_TPL_PATH, "r", encoding="utf-8") as f:
			return json.load(f) or {}
	except Exception:
		return {}

def _save_tpl(data):
	import json
	with open(_TPL_PATH, "w", encoding="utf-8") as f:
		json.dump(data, f, ensure_ascii=False, indent=2)

@app.get("/templates")
def list_templates():
	return _load_tpl()

@app.post("/templates/{name}")
def upsert_template(name: str, body: Dict[str, Any]):
	data = _load_tpl(); data[name] = body
	_save_tpl(data)
	return {"ok": True}

@app.delete("/templates/{name}")
def delete_template(name: str):
	data = _load_tpl(); data.pop(name, None)
	_save_tpl(data)
	return {"ok": True}

if __name__ == "__main__":
	import uvicorn
	uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "8080")))
