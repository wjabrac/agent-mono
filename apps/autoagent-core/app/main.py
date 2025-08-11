from fastapi import FastAPI, Query
from pydantic import BaseModel
from typing import List, Dict, Any
import os
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest, CollectorRegistry, REGISTRY
from core.agentControl import execute_steps
app = FastAPI(title="autoagent-core")
class StepModel(BaseModel):
    tool: str
    args: Dict[str, Any]
class RunModel(BaseModel):
    prompt: str
    steps: List[StepModel]
@app.get("/health")
def health():
    return {"ok": True}
@app.get("/metrics")
def metrics():
    return Response(content=generate_latest(REGISTRY), media_type=CONTENT_TYPE_LATEST)  # type: ignore
from fastapi import Response
@app.post("/run")
def run_agent(req: RunModel, thread: str | None = Query(default=None), tags: List[str] | None = Query(default=None)):
    return execute_steps(req.prompt, [s.dict() for s in req.steps], thread_id=thread, tags=tags or [])
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
    handle = await client.start_workflow(
        AgentWorkflow.run,
        AgentWorkflowInput(prompt=req.prompt, steps=[s.dict() for s in req.steps], thread=thread, tags=tags or []),
        id=wid,
        task_queue="agent-tq",
    )
    return {"workflow_id": handle.id, "run_id": handle.run_id}
