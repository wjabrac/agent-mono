import os
from typing import Dict, Any
from pydantic import BaseModel, Field
from core.tools.registry import ToolSpec, register
from core.instrumentation import instrument_tool
from core.trace_context import set_trace

# Minimal placeholder MCP adapter with local-safe registrations.
# Extend by actually connecting to MCP servers and mapping methods.

ALLOW_PAID = os.getenv("ALLOW_PAID_APIS", "false").lower() in ("1","true","yes")

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
	import requests
	r = requests.get(data.url, timeout=data.timeout)
	r.raise_for_status()
	return {"text": r.text[:200000]}

register(ToolSpec(name="mcp.http.get", input_model=HTTPGetInput, run=_mcp_http_get))

class SQLiteQueryInput(BaseModel):
	db_path: str
	query: str

@instrument_tool("mcp.sqlite.query")
def _mcp_sqlite_query(args: Dict[str, Any]) -> Dict[str, Any]:
	import sqlite3, json
	data = SQLiteQueryInput(**args)
	con = sqlite3.connect(data.db_path)
	cur = con.execute(data.query)
	cols = [d[0] for d in cur.description] if cur.description else []
	rows = cur.fetchall()
	con.close()
	return {"columns": cols, "rows": rows}

register(ToolSpec(name="mcp.sqlite.query", input_model=SQLiteQueryInput, run=_mcp_sqlite_query))

class ShellRunInput(BaseModel):
	cmd: str
	timeout: int = 10

@instrument_tool("mcp.shell.run")
def _mcp_shell_run(args: Dict[str, Any]) -> Dict[str, Any]:
	import subprocess
	data = ShellRunInput(**args)
	res = subprocess.run(data.cmd, shell=True, capture_output=True, text=True, timeout=data.timeout)
	return {"stdout": (res.stdout or "")[-200000:], "stderr": (res.stderr or "")[-50000:], "returncode": res.returncode}

register(ToolSpec(name="mcp.shell.run", input_model=ShellRunInput, run=_mcp_shell_run))

class GitStatusInput(BaseModel):
	repo: str

@instrument_tool("mcp.git.status")
def _mcp_git_status(args: Dict[str, Any]) -> Dict[str, Any]:
	import subprocess
	data = GitStatusInput(**args)
	res = subprocess.run("git status --porcelain=v1", cwd=data.repo, shell=True, capture_output=True, text=True)
	return {"stdout": res.stdout}

register(ToolSpec(name="mcp.git.status", input_model=GitStatusInput, run=_mcp_git_status))

# Existing MCP integration left intact
# Add delegate and kb.search microtools for convenience

class DelegateInput(BaseModel):
        prompt: str
        thread_id: str | None = None
        tags: list[str] = Field(default_factory=list)
        override_steps: list[dict[str, Any]] | None = None

@instrument_tool("agent.delegate")
def _delegate(args: Dict[str, Any]) -> Dict[str, Any]:
	from core.agentControl import execute_steps
	p = args.get("prompt", "")
	thread = args.get("thread_id")
	steps = args.get("override_steps")
	return execute_steps(p, steps, thread_id=thread, tags=args.get("tags") or [])

register(ToolSpec(name="agent.delegate", input_model=DelegateInput, run=_delegate))

@instrument_tool("kb.search")
def _kb_search(args: Dict[str, Any]) -> Dict[str, Any]:
	try:
		from core.knowledge.search import semantic_query
	except Exception:
		return {"results": []}
	q = args.get("q") or args.get("query") or ""
	k = int(args.get("k", 5) or 5)
	return {"results": semantic_query(q, top_k=k)}

register(ToolSpec(name="kb.search", input_model=None, run=_kb_search))
