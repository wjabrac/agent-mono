from __future__ import annotations

import os
import socket
from typing import Any, Dict

from .events import emit
from .permissions import Decision, PermissionChecker
from .sandbox import Sandbox


class Executor:
    def __init__(self, checker: PermissionChecker) -> None:
        self.checker = checker

    def execute(self, plugin, cmd: str, args: Dict[str, Any], actor: str) -> Any:
        emit("before_command", plugin, cmd, args, actor)
        required_scopes = getattr(plugin.module, "COMMAND_SCOPES", {}).get(cmd, set())
        decision = self.checker.check(plugin.manifest.name, cmd, actor, required_scopes)
        ctx = {
            "actor": actor,
            "plugin": plugin.manifest.name,
            "command": cmd,
            "args": args,
        }
        if not decision.allowed:
            self.checker.record_outcome(decision, ctx)
            return {"denied": decision.reason}
        sandbox = Sandbox()
        ctx["sandbox"] = str(sandbox.path)
        old_socket = socket.socket
        if plugin.manifest.network == "none":
            def _blocked(*_, **__):
                raise PermissionError("network disabled")
            socket.socket = _blocked  # type: ignore
        try:
            result = plugin.module.commands[cmd](args, sandbox)
            emit("after_command", plugin, cmd, args, actor, result)
            self.checker.record_outcome(decision, ctx)
            return result
        except Exception as exc:  # pylint: disable=broad-except
            ctx["error"] = exc
            self.checker.record_outcome(Decision(False, "error"), ctx)
            emit("on_error", plugin, cmd, args, actor, exc)
            raise
        finally:
            socket.socket = old_socket
            sandbox.cleanup()
