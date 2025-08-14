from typing import List, Dict, Any, Optional
from temporalio import workflow, activity
from datetime import timedelta

@activity.defn
def run_steps(prompt: str, steps: List[Dict[str, Any]] | None, thread: Optional[str] = None, tags: Optional[List[str]] = None) -> Dict[str, Any]:
	from core.agentControl import execute_steps
	return execute_steps(prompt, steps, thread_id=thread, tags=tags or [])

@workflow.defn(name="AgentWorkflow")
class AgentWorkflow:
	@workflow.run
	async def run(self, prompt: str, steps: List[Dict[str, Any]] | None = None, thread: Optional[str] = None, tags: Optional[List[str]] = None) -> Dict[str, Any]:
		return await workflow.execute_activity(
			run_steps, prompt, steps, thread, tags, schedule_to_close_timeout=timedelta(minutes=10)
		)
