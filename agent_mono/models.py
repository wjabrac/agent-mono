"""Pydantic models for agent runtime."""
from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class TaskSpec(BaseModel):
    goal: str
    constraints: List[str] = Field(default_factory=list)
    allowed_paths: List[Path] = Field(default_factory=list)
    forbidden_paths: List[Path] = Field(default_factory=list)
    success_criteria: List[str] = Field(default_factory=list)
    risk_level: int = 0
    plan: Optional[Dict] = None
    artifacts: Optional[Dict] = None

    def to_json(self) -> str:
        return self.model_dump_json()
