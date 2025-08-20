import os
import sqlite3
from typing import Any, Dict, List

from pydantic import BaseModel

from core.instrumentation import instrument_tool
from core.tools.manifest import load_manifest
from core.tools.registry import ToolSpec
from plugins.sandbox import run_in_sandbox

_DB_PATH = os.path.expanduser(os.getenv("AGENT_USAGE_DB", "~/.agent/usage.db"))


class IntrospectInput(BaseModel):
    pass


class IntrospectOutput(BaseModel):
    unused_plugins: List[str]
    failing_commands: List[str]
    helper_suggestions: List[str]


@instrument_tool("introspect")
def _run(args: Dict[str, Any]) -> Dict[str, Any]:
    IntrospectInput.model_validate(args)
    data = {"unused_plugins": [], "failing_commands": [], "helper_suggestions": []}
    mf = load_manifest()
    data["unused_plugins"] = [n for n, v in mf.items() if int(v.get("uses", 0)) == 0]
    if os.path.exists(_DB_PATH):
        conn = sqlite3.connect(_DB_PATH)
        rows = conn.execute(
            "SELECT command, exit_code, COUNT(*) FROM runs GROUP BY command, exit_code"
        ).fetchall()
        conn.close()
        failing = [cmd for cmd, code, _ in rows if code != 0]
        data["failing_commands"] = sorted(set(failing))
        counts: Dict[str, int] = {}
        for cmd, _, cnt in rows:
            counts[cmd] = counts.get(cmd, 0) + cnt
        data["helper_suggestions"] = [cmd for cmd, cnt in counts.items() if cnt >= 3]
    return IntrospectOutput(**data).model_dump()


spec = ToolSpec(
    name="introspect",
    input_model=IntrospectInput,
    output_model=IntrospectOutput,
    run=run_in_sandbox(_run),
)
