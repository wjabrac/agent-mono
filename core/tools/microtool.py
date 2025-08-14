from typing import Any, Callable, Dict, List, Optional
from pydantic import BaseModel
from core.tools.registry import ToolSpec, register
from core.instrumentation import instrument_tool
from core.tools.manifest import ensure_tool_entry


class MicrotoolSpec(BaseModel):
	name: str
	description: str = ""
	tags: List[str] = []
	input_model: Optional[type[BaseModel]] = None


def microtool(name: str, *, description: str = "", tags: List[str] | None = None, input_model: Optional[type[BaseModel]] = None) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
	def decorator(fn: Callable[..., Any]) -> Callable[..., Any]:
		mt_spec = MicrotoolSpec(name=name, description=description, tags=tags or [], input_model=input_model)
		setattr(fn, "_microtool_spec", mt_spec)
		# Ensure manifest entry exists early
		ensure_tool_entry(name, path="", tags=mt_spec.tags, composite_of=[], description=mt_spec.description)
		return fn
	return decorator


def build_toolspec_from_microtool(fn: Callable[..., Any]) -> ToolSpec:
	mt: MicrotoolSpec = getattr(fn, "_microtool_spec")
	@instrument_tool(mt.name)
	def _run(args: Dict[str, Any]) -> Dict[str, Any]:
		# Pass dict as kwargs; normalize return to dict
		res = fn(**args) if isinstance(args, dict) else fn(args)
		if isinstance(res, dict):
			return res
		return {"result": res}
	return ToolSpec(name=mt.name, input_model=mt.input_model, run=_run)