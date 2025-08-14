import os
from dataclasses import dataclass
from typing import List, Dict, Any, Optional

import sentry_sdk
from temporalio import workflow, activity

SENTRY_DSN = os.getenv("SENTRY_DSN")
if SENTRY_DSN:
    sentry_sdk.init(dsn=SENTRY_DSN, traces_sample_rate=1.0)


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
        return await workflow.execute_activity(
            run_steps, inp, schedule_to_close_timeout=timedelta(minutes=10)
        )


from datetime import timedelta
