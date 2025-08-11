import os, asyncio
from temporalio.worker import Worker
from temporalio.client import Client
from workflow import AgentWorkflow, run_steps
from prometheus_client import start_http_server
async def main():
    start_http_server(9109)  # worker metrics
    client = await Client.connect(os.getenv("TEMPORAL_HOST","temporal:7233"))
    worker = Worker(client, task_queue="agent-tq", workflows=[AgentWorkflow], activities=[run_steps])
    await worker.run()
if __name__ == "__main__":
    asyncio.run(main())
