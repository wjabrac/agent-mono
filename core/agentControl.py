from typing import Dict, Any, List, Optional, Set
from pydantic import BaseModel
from core.tools.registry import discover, get, _REGISTRY  # type: ignore
from core.trace_context import set_trace
from core.observability.trace import start_trace, log_event
from core.observability.metrics import (
    tool_calls_total,
    tool_latency_ms,
    tool_tokens_total,
)
import time
discover("plugins")

# --------------- Planner (local-first) ---------------

def _local_llm_available() -> bool:
    return os.getenv("OLLAMA_HOST") is not None

def _rule_based_plan(prompt: str) -> List[Dict[str, Any]]:
    # Extremely lightweight heuristic: map keywords to tools
    steps: List[Dict[str, Any]] = []
    p = prompt.lower()
    if "http" in p or "url" in p or "web" in p:
        steps.append({"tool": "web_fetch", "args": {"url": "https://example.com"}})
    if ".pdf" in p:
        steps.append({"tool": "pdf_text", "args": {"path": "./document.pdf"}})
    return steps or [{"tool": "web_fetch", "args": {"url": "https://example.com"}}]

try:
    import httpx
except Exception:
    httpx = None  # optional

def plan_steps(prompt: str) -> List[Dict[str, Any]]:
    # Prefer local LLM via Ollama if available, else fallback to rules
    if _local_llm_available() and httpx:
        try:
            # Minimal Ollama prompt to propose tools from registry
            tool_list = ", ".join(sorted(_REGISTRY.keys()))
            q = f"You are a planner. Given a task: '{prompt}', propose a short ordered JSON list of steps using tools from: [{tool_list}]. Each step: {{tool, args}}."
            base = os.getenv("OLLAMA_HOST", "http://localhost:11434").rstrip("/")
            r = httpx.post(f"{base}/api/generate", json={"model": os.getenv("OLLAMA_MODEL","llama3.1:8b"), "prompt": q, "stream": False}, timeout=8)
            r.raise_for_status()
            txt = r.json().get("response","[]")
            try:
                steps = json.loads(txt)
                if isinstance(steps, list):
                    return steps
            except Exception:
                pass
        except Exception:
            pass
    return _rule_based_plan(prompt)

# --------------- Execution policy (retries, timeouts, fallbacks, cache) ---------------

class Step(BaseModel):
    tool: str
    args: Dict[str, Any]
def execute_steps(prompt: str, steps: List[Dict[str, Any]], thread_id=None, tags=None) -> Dict[str, Any]:
    trace_id = start_trace(thread_id)
    set_trace(thread_id, trace_id, tags or [])
    label_tags = ",".join(sorted(tags or []))
    out = []
    for st in steps:
        s = Step(**st)
        log_event(
            trace_id,
            "decision",
            "planner:step",
            {"tool": s.tool, "args": s.args, "tags": tags or []},
        )
        spec = get(s.tool)
        t0 = time.time()
        ok = "true"
        tokens = 0
        try:
            res = spec.run(s.args)
            # Attempt to extract token usage for budget tracking.
            if isinstance(res, dict):
                usage = res.get("usage") or {}
                tokens = (
                    usage.get("total_tokens")
                    or res.get("total_tokens")
                    or res.get("token_usage", 0)
                )
            out.append({"tool": s.tool, "output": res})
        except Exception:
            ok = "false"
            raise
        finally:
            tool_calls_total.labels(s.tool, ok, label_tags).inc()
            tool_latency_ms.labels(s.tool, label_tags).observe((time.time() - t0) * 1000.0)
            if tokens:
                tool_tokens_total.labels(s.tool, label_tags).inc(tokens)
    return {"trace_id": trace_id, "outputs": out}
