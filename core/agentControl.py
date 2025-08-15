from typing import Dict, Any, List, Optional, Set
from pydantic import BaseModel
from core.tools.registry import discover, get, _REGISTRY  # type: ignore
from core.trace_context import set_trace
from core.observability.trace import start_trace, log_event
from core.observability.metrics import tool_calls_total, tool_latency_ms, tool_skipped_total
from core.memory.db import cache_get, cache_put, kv_put
import time, os, json, hashlib, concurrent.futures, threading, asyncio, inspect

# Manifest usage tracking
try:
	from core.tools.manifest import register_usage as register_usage_metric  # type: ignore
except Exception:
	def register_usage_metric(name: str, success: bool = True, tags=None, path: str = "", description: str = ""):
		return

# Discover all plugins
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

# Advanced planning expansion (conditionals/loops)
try:
    from core.planning.advanced import expand_plan  # type: ignore
except Exception:
    def expand_plan(steps: List[Dict[str, Any]]) -> List[Dict[str, Any]]:  # type: ignore
        return steps

# Reflection checkpoints
try:
    from core.planning.reflection import maybe_replan  # type: ignore
except Exception:
    def maybe_replan(trace_id: str, prompt: str, outputs: List[Dict[str, Any]]):  # type: ignore
        return []

# Policy and sandbox
try:
    from core.security.policy import check_tool_allowed, is_risky_tool, enforce_output_limits  # type: ignore
    from core.security.sandbox import run_in_sandbox  # type: ignore
except Exception:
    def check_tool_allowed(tool_name: str, args: Dict[str, Any]) -> None:  # type: ignore
        return
    def is_risky_tool(tool_name: str) -> bool:  # type: ignore
        return False
    def enforce_output_limits(tool_name: str, output: Any) -> None:  # type: ignore
        return
    def run_in_sandbox(fn, args, timeout_s=20):  # type: ignore
        return fn(args)


def plan_steps(prompt: str) -> List[Dict[str, Any]]:
    # Prefer local LLM via Ollama if available, else fallback to rules
    if _local_llm_available() and httpx:
        try:
            # Minimal Ollama prompt to propose tools from registry
            tool_list = ", ".join(sorted(_REGISTRY.keys()))
            q = f"You are a planner. Given a task: '{prompt}', propose a short ordered JSON list of steps using tools from: [{tool_list}]. Each step object must be of the form {{\"tool\": \"...\", \"args\": {{...}}}}."
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
    depends_on: Optional[List[str]] = None
    ttl_s: int = 0
    fallback_tool: Optional[str] = None
    timeout_s: int = 20
    retries: int = 1

_def_fallbacks: Dict[str, str] = {  # example mapping
    # "web_fetch": "web_fetch_alt",
}

_thread_local = threading.local()

def _args_hash(args: Dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(args, sort_keys=True).encode()).hexdigest()

def _run_with_policy(step: Step, trace_id: str) -> Dict[str, Any]:
    start = time.time()
    spec = get(step.tool)
    check_tool_allowed(step.tool, step.args)
    cache_key = _args_hash(step.args)
    if step.ttl_s:
        cached = cache_get(step.tool, cache_key)
        if cached is not None:
            tool_calls_total.labels(step.tool, "true").inc()
            tool_latency_ms.labels(step.tool).observe((time.time()-start)*1000.0)
            log_event(trace_id, "decision", "executor:cache_hit", {"tool": step.tool})
            return {"tool": step.tool, "output": json.loads(cached)}
    last_err = None
    for attempt in range(max(1, step.retries)):
        t0 = time.time()
        try:
            # Timeout wrapper using thread pool to keep minimal deps
            if is_risky_tool(step.tool):
                # execute in a sandboxed subprocess for risky tools
                res = run_in_sandbox(spec.run, step.args, timeout_s=step.timeout_s)
            else:
                with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
                    fut = ex.submit(spec.run, step.args)
                    res = fut.result(timeout=step.timeout_s)
                    if inspect.isawaitable(res):
                        res = asyncio.run(res)
            enforce_output_limits(step.tool, res)
            tool_calls_total.labels(step.tool, "true").inc()
            tool_latency_ms.labels(step.tool).observe((time.time()-t0)*1000.0)
            if step.ttl_s:
                try:
                    cache_put(step.tool, cache_key, json.dumps(res), ttl_s=step.ttl_s)
                except Exception:
                    pass
            try:
                register_usage_metric(step.tool, success=True)
            except Exception:
                pass
            log_event(trace_id, "decision", "tool:result", {"tool": step.tool, "success": True})
            return {"tool": step.tool, "output": res}
        except Exception as e:
            last_err = e
            tool_calls_total.labels(step.tool, "false").inc()
            log_event(trace_id, "decision", "tool:result", {"tool": step.tool, "success": False, "error": type(e).__name__, "msg": str(e), "attempt": attempt+1})
            log_event(trace_id, "decision", "executor:error", {"tool": step.tool, "error": type(e).__name__, "msg": str(e), "attempt": attempt+1})
            time.sleep(min(1.5**attempt, 5))
    # fallback
    fb = step.fallback_tool or _def_fallbacks.get(step.tool)
    if fb:
        try:
            fb_spec = get(fb)
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
                fut = ex.submit(fb_spec.run, step.args)
                res = fut.result(timeout=step.timeout_s)
            enforce_output_limits(fb, res)
            log_event(trace_id, "decision", "executor:fallback", {"from": step.tool, "to": fb})
            tool_calls_total.labels(fb, "true").inc()
            try:
                register_usage_metric(fb, success=True)
            except Exception:
                pass
            return {"tool": fb, "output": res}
        except Exception as e:
            log_event(trace_id, "decision", "executor:fallback_error", {"from": step.tool, "to": fb, "error": type(e).__name__})
    try:
        register_usage_metric(step.tool, success=False)
    except Exception:
        pass
    raise last_err or RuntimeError("tool_failed")

# --------------- DAG / parallel scheduling ---------------

def _toposort(steps: List[Step]) -> List[Step]:
    name_to_idx = {f"{i}:{s.tool}": i for i, s in enumerate(steps)}
    indeg = {i: 0 for i in range(len(steps))}
    edges: Dict[int, Set[int]] = {i: set() for i in range(len(steps))}
    for i, s in enumerate(steps):
        if not s.depends_on:
            continue
        for dep in s.depends_on:
            for j, prev in enumerate(steps):
                if prev.tool == dep:
                    edges[j].add(i)
                    indeg[i] += 1
    # Kahn
    q = [i for i in indeg if indeg[i] == 0]
    order: List[int] = []
    while q:
        i = q.pop(0)
        order.append(i)
        for v in edges[i]:
            indeg[v] -= 1
            if indeg[v] == 0:
                q.append(v)
    return [steps[i] for i in order] if len(order) == len(steps) else steps

# --------------- Human-in-the-loop defaults for multi-phase ---------------

def _needs_hitl(steps: List[Step]) -> bool:
    # heuristic: multi-step or any depends_on => treat as multi-phase
    return len(steps) > 1 or any(s.depends_on for s in steps)

# Hook for UI/CLI: pause and request approval between phases
# For now, reads env HITL_DEFAULT=true to require approval on multi-phase

def _await_human_approval(phase_name: str, steps: List[Step]) -> None:
    if os.getenv("HITL_DEFAULT", "true").lower() in ("1","true","yes"):  # default require HITL
        log_event(_thread_local.trace_id, "decision", "hitl:await", {"phase": phase_name, "steps": [s.tool for s in steps]})
        # Minimal blocking prompt in serverless env: wait for a flag file
        token = os.getenv("HITL_TOKEN", "/run/hitl.ok")
        path = token if os.path.isabs(token) else os.path.join(os.getenv("LOCAL_ROOT","."), token)
        while not os.path.exists(path):
            time.sleep(1)
        try:
            os.remove(path)
        except Exception:
            pass

# --------------- Main entrypoint ---------------

def execute_steps(prompt: str, steps: List[Dict[str, Any]] | None = None, thread_id=None, tags=None) -> Dict[str, Any]:
    trace_id = start_trace(thread_id); _thread_local.trace_id = trace_id
    set_trace(thread_id, trace_id, tags or [])
    out = []
    # Plan if not provided
    if not steps:
        planned = plan_steps(prompt)
        planned = expand_plan(planned)
        log_event(trace_id, "decision", "planner:proposed", {"steps": planned})
        steps = planned
    # Parse and sort
    parsed: List[Step] = []
    for st in steps:
        parsed.append(Step(**st))
    if _needs_hitl(parsed):
        _await_human_approval("phase:plan_review", parsed)
    schedule = _toposort(parsed)
    # Parallel execution by waves
    # Determine waves by indegree (simple levelization)
    remaining = set(range(len(schedule)))
    deps: Dict[int, Set[int]] = {i: set() for i in range(len(schedule))}
    for i, s in enumerate(schedule):
        if s.depends_on:
            for j, ps in enumerate(schedule):
                if ps.tool in (s.depends_on or []):
                    deps[i].add(j)
    while remaining:
        ready = [i for i in remaining if deps[i] <= (set(range(len(schedule))) - remaining)]
        if not ready:
            # cycle or unresolved
            for i in list(remaining):
                tool_skipped_total.labels(schedule[i].tool, "blocked").inc()
                log_event(trace_id, "decision", "executor:skip", {"tool": schedule[i].tool, "reason": "blocked"})
                remaining.remove(i)
            break
        wave = [schedule[i] for i in ready]
        # hot-reload registry if enabled between waves
        try:
            from core.tools.registry import reload_if_needed  # type: ignore
            reload_if_needed()
        except Exception:
            pass
        if len(wave) > 1 and _needs_hitl(wave):
            _await_human_approval("phase:wave_start", wave)
        with concurrent.futures.ThreadPoolExecutor(max_workers=min(4, len(wave))) as ex:
            futures = {}
            for s in wave:
                try:
                    spec = get(s.tool)
                except KeyError:
                    log_event(trace_id, "decision", "tool:lookup_error", {"tool": s.tool})
                    raise
                if os.getenv("HITL_PER_STEP", "false").lower() in ("1","true","yes"):
                    _await_human_approval("phase:step", [s])
                futures[ex.submit(_run_with_policy, s, trace_id)] = s
            for fut, s in list(futures.items()):
                try:
                    res = fut.result()
                    out.append(res)
                    # persist to session memory for contextual recall
                    try:
                        kv_put(thread_id, f"step:{s.tool}", json.dumps(res))
                    except Exception:
                        pass
                except Exception as e:
                    # Mark dependents as prior_error
                    for i in list(remaining):
                        if s.tool in (schedule[i].depends_on or []):
                            tool_skipped_total.labels(schedule[i].tool, "prior_error").inc()
                            log_event(trace_id, "decision", "executor:skip", {"tool": schedule[i].tool, "reason": "prior_error"})
                            remaining.discard(i)
                finally:
                    remaining.discard(schedule.index(s))
    # Reflection checkpoint and optional replanning pass
    extra = maybe_replan(trace_id, prompt, out)
    if extra:
        for st in extra:
            try:
                res = _run_with_policy(Step(**st), trace_id)
                out.append(res)
                try:
                    kv_put(thread_id, f"step:{st.get('tool','')}", json.dumps(res))  # type: ignore
                except Exception:
                    pass
            except Exception:
                pass
    return {"trace_id": trace_id, "outputs": out}
