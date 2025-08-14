from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Set

from . import audit


@dataclass
class Decision:
    allowed: bool
    reason: str = ""
    rate_limited: bool = False


class PermissionChecker:
    """Default deny permission checker."""

    def __init__(self) -> None:
        self.scopes: Dict[str, Set[str]] = {}
        self.limits: Dict[str, int] = {}

    def register_plugin(self, name: str, scopes: Set[str], limit: int) -> None:
        self.scopes[name] = set(scopes)
        self.limits[name] = limit

    def check(self, tool: str, command: str, actor: str, scopes: Set[str]) -> Decision:
        allowed_scopes = self.scopes.get(tool, set())
        if not scopes.issubset(allowed_scopes):
            return Decision(False, "missing_scope")
        limit = self.limits.get(tool, 30)
        if audit.rate_check(tool, command, actor, limit):
            return Decision(False, "rate_limited", rate_limited=True)
        return Decision(True)

    def record_outcome(self, decision: Decision, context: dict) -> None:
        audit.record(
            "allow" if decision.allowed else "deny",
            actor=context.get("actor", ""),
            plugin=context.get("plugin", ""),
            command=context.get("command", ""),
            args=context.get("args", {}),
            sandbox_path=context.get("sandbox"),
            rate_limited=decision.rate_limited,
            error=context.get("error"),
        )
