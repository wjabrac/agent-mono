from fastapi import FastAPI, Query
from pydantic import BaseModel
from typing import List, Dict, Any
import os
from core.agentControl import execute_steps, plan_steps
from core.observability.insights import compute_insights
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
	token = os.getenv("HITL_TOKEN", "hitl.ok")	
	path = os.path.join(os.getenv("LOCAL_ROOT","."), token)
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
	from services.temporal_worker.workflow import AgentWorkflowInput  # type: ignore
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
	from services.temporal_worker.workflow import AgentWorkflow  # type: ignore
	inp = AgentWorkflowInput(prompt=req.prompt, steps=(None if req.steps is None else [s.dict() for s in req.steps]), thread=thread, tags=tags or [])
	handle = await client.start_workflow(
		AgentWorkflow.run,
		inp,
		id=wid,
		task_queue="agent-tq",
	)
	return {"workflow_id": handle.id, "run_id": handle.run_id}

if __name__ == "__main__":
	import uvicorn
	uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "8080")))
