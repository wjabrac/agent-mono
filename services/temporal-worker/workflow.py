from __future__ import annotations

from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from datetime import timedelta

from temporalio import workflow, activity
from opentelemetry import trace as _trace

_TRACER = _trace.get_tracer("core.workflow", "0.1.0")


@dataclass
class AgentWorkflowInput:
    prompt: str
    steps: List[Dict[str, Any]]
    thread: Optional[str] = None
    tags: Optional[List[str]] = None


@activity.defn
def run_steps(inp: AgentWorkflowInput) -> Dict[str, Any]:
    from core.agentControl import execute_steps
    return execute_steps(inp.prompt, inp.steps, thread_id=inp.thread, tags=inp.tags or [])


@workflow.defn(name="AgentWorkflow")
class AgentWorkflow:
    @workflow.run
    async def run(self, inp: AgentWorkflowInput) -> Dict[str, Any]:
        with _TRACER.start_as_current_span("AgentWorkflow.run") as span:
            span.set_attribute("prompt.len", len(inp.prompt or ""))
            span.set_attribute("steps.count", len(inp.steps or []))
            if inp.thread:
                span.set_attribute("thread", inp.thread)
            if inp.tags:
                span.set_attribute("tags", ",".join(inp.tags))
            return await workflow.execute_activity(
                run_steps, inp, schedule_to_close_timeout=timedelta(minutes=10)
            )
