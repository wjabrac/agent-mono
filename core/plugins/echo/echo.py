from __future__ import annotations

from pathlib import Path
from typing import Any, Dict


COMMAND_SCOPES = {
    "write": {"fs.temp"},
    "net": set(),
}


def write(args: Dict[str, Any], sandbox) -> Dict[str, Any]:
    path = sandbox.resolve(args["path"])
    Path(path).write_text(args.get("content", ""))
    return {"written": str(path)}


def net(args: Dict[str, Any], sandbox):
    import socket
    s = socket.socket()
    s.connect(("example.com", 80))
    return {"sock": True}


commands = {"write": write, "net": net}
