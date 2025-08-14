from __future__ import annotations

import inspect
import time
from typing import Dict, Any, Optional, List

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from opentelemetry import trace as _trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

from core.observability.metrics import (
    tool_calls_total,
    tool_latency_ms,
    tool_skipped_total,
    llm_calls_total,
    llm_latency_ms,
)
from autoagent.registry import registry  # expects your existing registry facade
from autoagent import MetaChain
from autoagent.types import Agent, Response

_tp = TracerProvider()
_tp.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))
_trace.set_tracer_provider(_tp)
_TRACER = _trace.get_tracer("core.server", "0.1.0")

app = FastAPI(title="MetaChain API")
FastAPIInstrumentor().instrument_app(app)


class ToolRequest(BaseModel):
    args: Dict[str, Any]


class AgentRequest(BaseModel):
    model: str
    query: str
    context_variables: Optional[Dict[str, Any]] = {}


class Message(BaseModel):
    role: str
    content: str


class AgentResponse(BaseModel):
    result: str
    messages: List
    agent_name: str


@app.on_event("startup")
def create_tool_endpoints() -> None:
    for tool_name, tool_func in registry.tools.items():
        async def create_tool_endpoint(request: ToolRequest, func=tool_func, name=tool_name):
            t0 = time.perf_counter()
            ok = "false"
            with _TRACER.start_as_current_span("tool.call") as span:
                span.set_attribute("tool.name", name)
                try:
                    sig = inspect.signature(func)
                    required_params = {
                        pname
                        for pname, param in sig.parameters.items()
                        if param.default is inspect.Parameter.empty
                    }
                    if not all(param in request.args for param in required_params):
                        missing = sorted(required_params - request.args.keys())
                        span.set_attribute("tool.missing_params", ",".join(missing))
                        tool_skipped_total.labels(name, "missing_params").inc()
                        raise HTTPException(status_code=400, detail=f"Missing required parameters: {missing}")

                    result = func(**request.args)
                    ok = "true"
                    return {"status": "success", "result": result}
                except HTTPException:
                    raise
                except Exception as e:
                    span.set_attribute("error", True)
                    span.set_attribute("error.type", type(e).__name__)
                    span.set_attribute("error.msg", str(e))
                    raise HTTPException(status_code=400, detail=str(e))
                finally:
                    dt_ms = (time.perf_counter() - t0) * 1000.0
                    tool_calls_total.labels(name, ok).inc()
                    tool_latency_ms.labels(name).observe(dt_ms)

        endpoint = create_tool_endpoint
        endpoint.__name__ = f"tool_{tool_name}"
        app.post(f"/tools/{tool_name}")(endpoint)


@app.on_event("startup")
def create_agent_endpoints() -> None:
    for agent_name, agent_factory in registry.agents.items():
        async def create_agent_endpoint(request: AgentRequest, factory=agent_factory, name=agent_name) -> AgentResponse:
            t0 = time.perf_counter()
            ok = "false"
            tags = ""
            with _TRACER.start_as_current_span("agent.run") as span:
                span.set_attribute("agent.name", name)
                span.set_attribute("agent.model", request.model)
                span.set_attribute("agent.query.len", len(request.query or ""))
                try:
                    agent: Agent = factory(model=request.model)
                    tags = ",".join(request.context_variables.get("tags", [])) if request.context_variables else ""
                    span.set_attribute("agent.tags", tags)
                    mc = MetaChain()
                    messages = [{"role": "user", "content": request.query}]
                    response: Response = mc.run(
                        agent=agent,
                        messages=messages,
                        context_storage=request.context_variables,
                        debug=True,
                    )
                    ok = "true"
                    return AgentResponse(
                        result=response.messages[-1]["content"],
                        messages=response.messages,
                        agent_name=agent.name,
                    )
                except HTTPException:
                    raise
                except Exception as e:
                    span.set_attribute("error", True)
                    span.set_attribute("error.type", type(e).__name__)
                    span.set_attribute("error.msg", str(e))
                    raise HTTPException(status_code=400, detail=f"Agent execution failed: {str(e)}")
                finally:
                    dt_ms = (time.perf_counter() - t0) * 1000.0
                    llm_calls_total.labels(request.model, ok, tags).inc()
                    llm_latency_ms.labels(request.model, tags).observe(dt_ms)

        endpoint = create_agent_endpoint
        endpoint.__name__ = f"agent_{agent_name}"
        app.post(f"/agents/{agent_name}/run")(endpoint)


@app.get("/agents")
async def list_agents():
    return {
        name: {
            "docstring": info.docstring,
            "args": info.args,
            "file_path": info.file_path,
        }
        for name, info in registry.agents_info.items()
    }


@app.get("/agents/{agent_name}")
async def get_agent_info(agent_name: str):
    if agent_name not in registry.agents_info:
        raise HTTPException(status_code=404, detail=f"Agent {agent_name} not found")
    info = registry.agents_info[agent_name]
    return {
        "name": agent_name,
        "docstring": info.docstring,
        "args": info.args,
        "file_path": info.file_path,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
