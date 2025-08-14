import os
import subprocess
from typing import Dict, Any

from pydantic import BaseModel, Field
from core.tools.registry import ToolSpec, register
from core.instrumentation import instrument_tool
from core.trace_context import set_trace  # noqa: F401  (kept for parity with prior adapter)


class FSReadInput(BaseModel):
    path: str


@instrument_tool("mcp.fs.read")
def _mcp_fs_read(args: Dict[str, Any]) -> Dict[str, Any]:
    data = FSReadInput(**args)
    with open(data.path, "r", encoding="utf-8", errors="ignore") as f:
        return {"text": f.read()}


register(ToolSpec(name="mcp.fs.read", input_model=FSReadInput, run=_mcp_fs_read))


class HTTPGetInput(BaseModel):
    url: str
    timeout: int = 15


@instrument_tool("mcp.http.get")
def _mcp_http_get(args: Dict[str, Any]) -> Dict[str, Any]:
    data = HTTPGetInput(**args)
    import requests  # local import to avoid CI import failures at module load
    r = requests.get(data.url, timeout=data.timeout)
    r.raise_for_status()
    return {"text": r.text[:200000]}


register(ToolSpec(name="mcp.http.get", input_model=HTTPGetInput, run=_mcp_http_get))


class SQLiteQueryInput(BaseModel):
    db_path: str
    query: str


@instrument_tool("mcp.sqlite.query")
def _mcp_sqlite_query(args: Dict[str, Any]) -> Dict[str, Any]:
    import sqlite3  # local import
    data = SQLiteQueryInput(**args)
    con = sqlite3.connect(data.db_path)
    try:
        cur = con.execute(data.query)
        cols = [d[0] for d in cur.description] if cur.description else []
        rows = cur.fetchall()
        return {"columns": cols, "rows": rows}
    finally:
        con.close()


register(ToolSpec(name="mcp.sqlite.query", input_model=SQLiteQueryInput, run=_mcp_sqlite_query))


class ShellRunInput(BaseModel):
    cmd: str
    timeout: int = 10


@instrument_tool("mcp.shell.run")
def _mcp_shell_run(args: Dict[str, Any]) -> Dict[str, Any]:
    data = ShellRunInput(**args)
    res = subprocess.run(
        data.cmd,
        shell=True,
        capture_output=True,
        text=True,
        timeout=data.timeout,
    )
    return {
        "stdout": (res.stdout or "")[-200000:],
        "stderr": (res.stderr or "")[-50000:],
        "returncode": res.returncode,
    }


register(ToolSpec(name="mcp.shell.run", input_model=ShellRunInput, run=_mcp_shell_run))


class GitStatusInput(BaseModel):
    repo: str


@instrument_tool("mcp.git.status")
def _mcp_git_status(args: Dict[str, Any]) -> Dict[str, Any]:
    data = GitStatusInput(**args)
    res = subprocess.run(
        "git status --porcelain=v1",
        cwd=data.repo,
        shell=True,
        capture_output=True,
        text=True,
    )
    return {"stdout": res.stdout}


register(ToolSpec(name="mcp.git.status", input_model=GitStatusInput, run=_mcp_git_status))


class DelegateInput(BaseModel):
    prompt: str
    thread_id: str | None = None
    tags: list[str] = Field(default_factory=list)
    override_steps: list[dict[str, Any]] | None = None


@instrument_tool("agent.delegate")
def _delegate(args: Dict[str, Any]) -> Dict[str, Any]:
    from core.agentControl import execute_steps  # local import to avoid heavy deps at import time
    p = args.get("prompt", "")
    thread = args.get("thread_id")
    steps = args.get("override_steps")
    return execute_steps(p, steps, thread_id=thread, tags=args.get("tags") or [])


register(ToolSpec(name="agent.delegate", input_model=DelegateInput, run=_delegate))


@instrument_tool("kb.search")
def _kb_search(args: Dict[str, Any]) -> Dict[str, Any]:
    try:
        from core.knowledge.search import semantic_query  # local import
    except Exception:
        return {"results": []}
    q = args.get("q") or args.get("query") or ""
    k = int(args.get("k", 5) or 5)
    return {"results": semantic_query(q, top_k=k)}


register(ToolSpec(name="kb.search", input_model=None, run=_kb_search))

# -----------------------------
# Math eval (sandboxed to math module)
# -----------------------------
class MathEvalInput(BaseModel):
    expr: str


@instrument_tool("mcp.math.eval")
def _mcp_math_eval(args: Dict[str, Any]) -> Dict[str, Any]:
    data = MathEvalInput(**args)
    import math
    try:
        result = eval(data.expr, {"__builtins__": {}}, vars(math))
        return {"result": result}
    except Exception as e:
        return {"error": str(e)}


register(ToolSpec(name="mcp.math.eval", input_model=MathEvalInput, run=_mcp_math_eval))


class DDGSearchInput(BaseModel):
    query: str
    max_results: int = 5


@instrument_tool("mcp.search.ddg")
def _mcp_search_ddg(args: Dict[str, Any]) -> Dict[str, Any]:
    import requests
    data = DDGSearchInput(**args)
    try:
        r = requests.get(
            "https://duckduckgo.com/",
            params={"q": data.query, "format": "json", "no_redirect": 1},
            timeout=10,
        )
        r.raise_for_status()
        js = r.json()
        topics = js.get("RelatedTopics", []) if isinstance(js, dict) else []
        return {"results": topics[: data.max_results]}
    except Exception:
        return {"results": []}


register(ToolSpec(name="mcp.search.ddg", input_model=DDGSearchInput, run=_mcp_search_ddg))


class MessageInput(BaseModel):
    thread_id: str
    sender: str
    recipient: str
    content: str


@instrument_tool("agent.message")
def _agent_message(args: Dict[str, Any]) -> Dict[str, Any]:
    from core.memory import db
    data = MessageInput(**args)
    db.save_message(data.thread_id, data.sender, data.recipient, data.content)
    return {"stored": True}


register(ToolSpec(name="agent.message", input_model=MessageInput, run=_agent_message))


class InboxInput(BaseModel):
    thread_id: str
    recipient: str


@instrument_tool("agent.inbox")
def _agent_inbox(args: Dict[str, Any]) -> Dict[str, Any]:
    from core.memory import db
    data = InboxInput(**args)
    msgs = db.fetch_messages(data.thread_id, data.recipient)
    return {"messages": msgs}


register(ToolSpec(name="agent.inbox", input_model=InboxInput, run=_agent_inbox))
