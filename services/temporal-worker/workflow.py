import os
from dataclasses import dataclass
from typing import List, Dict, Any, Optional

from temporalio import workflow, activity

# Optional OpenTelemetry tracing
try:  # pragma: no cover - instrumentation is optional
    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import (
        BatchSpanProcessor,
        ConsoleSpanExporter,
    )

    trace.set_tracer_provider(TracerProvider())
    trace.get_tracer_provider().add_span_processor(
        BatchSpanProcessor(ConsoleSpanExporter())
    )
    _TRACER = trace.get_tracer(__name__)
except Exception:  # pragma: no cover - missing dependency
    _TRACER = None


@dataclass
class AgentWorkflowInput:
    prompt: str
    steps: List[Dict[str, Any]]
    thread: Optional[str] = None
    tags: Optional[List[str]] = None


@activity.defn
def run_steps(inp: AgentWorkflowInput) -> Dict[str, Any]:
    from core.agentControl import execute_steps

    return execute_steps(
        inp.prompt, inp.steps, thread_id=inp.thread, tags=inp.tags or []
    )


@workflow.defn
class AgentWorkflow:
    @workflow.run
    async def run(self, inp: AgentWorkflowInput) -> Dict[str, Any]:
        if _TRACER:
            with _TRACER.start_as_current_span("AgentWorkflow.run"):
                return await workflow.execute_activity(
                    run_steps, inp, schedule_to_close_timeout=timedelta(minutes=10)
                )
        return await workflow.execute_activity(
            run_steps, inp, schedule_to_close_timeout=timedelta(minutes=10)
        )


from datetime import timedelta
