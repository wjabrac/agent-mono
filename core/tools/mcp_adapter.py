import os
from typing import Dict, Any, Callable
from pydantic import BaseModel
from core.tools.registry import ToolSpec, register

# Minimal placeholder MCP adapter with local-safe registrations.
# Extend by actually connecting to MCP servers and mapping methods.

ALLOW_PAID = os.getenv("ALLOW_PAID_APIS", "false").lower() in ("1","true","yes")

# Example: local-only shells/filesystem/http/sqlite/git wrappers can be registered here
# The implementations below are intentionally simple; replace with MCP client calls as you wire them.

class FSReadInput(BaseModel):
	path: str

@register(type="tool", name="mcp.fs.read", func_name="mcp_fs_read")
def mcp_fs_read(path: str) -> str:
	with open(path, "r", encoding="utf-8", errors="ignore") as f:
		return f.read()

class HTTPGetInput(BaseModel):
	url: str
	timeout: int = 15

@register(type="tool", name="mcp.http.get", func_name="mcp_http_get")
def mcp_http_get(url: str, timeout: int = 15) -> str:
	import requests
	r = requests.get(url, timeout=timeout)
	r.raise_for_status()
	return r.text[:200000]

class SQLiteQueryInput(BaseModel):
	db_path: str
	query: str

@register(type="tool", name="mcp.sqlite.query", func_name="mcp_sqlite_query")
def mcp_sqlite_query(db_path: str, query: str) -> str:
	import sqlite3, json
	con = sqlite3.connect(db_path)
	cur = con.execute(query)
	cols = [d[0] for d in cur.description] if cur.description else []
	rows = cur.fetchall()
	con.close()
	return json.dumps({"columns": cols, "rows": rows}, ensure_ascii=False)

class ShellRunInput(BaseModel):
	cmd: str
	timeout: int = 10

@register(type="tool", name="mcp.shell.run", func_name="mcp_shell_run")
def mcp_shell_run(cmd: str, timeout: int = 10) -> str:
	import subprocess
	res = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
	return (res.stdout or "")[-200000:]

class GitStatusInput(BaseModel):
	repo: str

@register(type="tool", name="mcp.git.status", func_name="mcp_git_status")
def mcp_git_status(repo: str) -> str:
	import subprocess
	res = subprocess.run("git status --porcelain=v1", cwd=repo, shell=True, capture_output=True, text=True)
	return res.stdout