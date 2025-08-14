import os
from typing import Dict, Optional, Any, List
import yaml

class BudgetExceeded(Exception):
    """Raised when a global or per-tool budget is exceeded."""

    def __init__(self, scope: str, limit: int, used: int, amount: int):
        self.scope = scope
        self.limit = limit
        self.used = used
        self.amount = amount
        super().__init__(f"{scope} budget exceeded: {used + amount}/{limit}")


class BudgetManager:
    """Manage token budgets across tools and globally.

    Budgets can be supplied via a YAML file or environment variables.
    Environment variables take precedence over YAML values.
    
    YAML format::
        global: 1000
        tools:
          web_fetch: 500
          pdf_text: 200
    
    Environment variables::
        BUDGET_GLOBAL=1000
        BUDGET_TOOL_WEB_FETCH=500
    """

    def __init__(self, config_path: Optional[str] = None):
        self.global_limit: Optional[int] = None
        self.tool_limits: Dict[str, int] = {}
        self.global_used = 0
        self.tool_used: Dict[str, int] = {}
        self.tag_limits: Dict[str, int] = {}
        self.tag_used: Dict[str, int] = {}

        path = config_path or os.environ.get("BUDGET_CONFIG")
        data: Dict[str, Any] = {}
        if path and os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}

        # load limits from YAML
        if "global" in data:
            self.global_limit = int(data["global"])
        tools_section = data.get("tools", {})
        for tool, limit in tools_section.items():
            self.tool_limits[tool] = int(limit)
        tags_section = data.get("tags", {})
        for tag, limit in tags_section.items():
            self.tag_limits[tag] = int(limit)

        # environment overrides
        env_global = os.environ.get("BUDGET_GLOBAL")
        if env_global is not None:
            self.global_limit = int(env_global)
        for key, value in os.environ.items():
            if key.startswith("BUDGET_TOOL_"):
                tool = key[len("BUDGET_TOOL_"):].lower()
                self.tool_limits[tool] = int(value)
            if key.startswith("BUDGET_TAG_"):
                tag = key[len("BUDGET_TAG_"):].lower()
                self.tag_limits[tag] = int(value)

    def remaining(self, tool: Optional[str] = None) -> Optional[int]:
        if tool:
            limit = self.tool_limits.get(tool)
            used = self.tool_used.get(tool, 0)
            if limit is None:
                return None
            return max(limit - used, 0)
        if self.global_limit is None:
            return None
        return max(self.global_limit - self.global_used, 0)

    def check_and_decrement(self, tool: str, amount: int, tags: Optional[List[str]] = None) -> None:
        tags = tags or []
        # Check global limit
        if self.global_limit is not None and self.global_used + amount > self.global_limit:
            raise BudgetExceeded("global", self.global_limit, self.global_used, amount)

        # Check tool-specific limit
        tool_limit = self.tool_limits.get(tool)
        used_tool = self.tool_used.get(tool, 0)
        if tool_limit is not None and used_tool + amount > tool_limit:
            raise BudgetExceeded(tool, tool_limit, used_tool, amount)

        # Check tag limits
        for tag in tags:
            limit = self.tag_limits.get(tag)
            used = self.tag_used.get(tag, 0)
            if limit is not None and used + amount > limit:
                raise BudgetExceeded(tag, limit, used, amount)

        # Decrement budgets
        self.global_used += amount
        self.tool_used[tool] = used_tool + amount
        for tag in tags:
            if tag in self.tag_limits:
                self.tag_used[tag] = self.tag_used.get(tag, 0) + amount

# Singleton helper
_manager: Optional[BudgetManager] = None

def get_budget_manager() -> BudgetManager:
    global _manager
    if _manager is None:
        _manager = BudgetManager()
    return _manager
