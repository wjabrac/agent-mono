from typing import Any, Callable, Dict, List, Optional
from pydantic import BaseModel, Field
from core.tools.registry import ToolSpec, register
from core.instrumentation import instrument_tool


class MicrotoolSpec(BaseModel):
	name: str
	description: str = ""
	tags: List[str] = Field(default_factory=list)
	input_model: Optional[type[BaseModel]] = None


def microtool(name: str, *, description: str = "", tags: List[str] | None = None, input_model: Optional[type[BaseModel]] = None) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
	def decorator(fn: Callable[..., Any]) -> Callable[..., Any]:
		mt_spec = MicrotoolSpec(name=name, description=description, tags=tags or [], input_model=input_model)
		setattr(fn, "_microtool_spec", mt_spec)
		# Defer manifest entry until discovery so file path is known
		return fn
	return decorator


def build_toolspec_from_microtool(fn: Callable[..., Any]) -> ToolSpec:
	import asyncio, inspect
	mt: MicrotoolSpec = getattr(fn, "_microtool_spec")
	is_async = inspect.iscoroutinefunction(fn)
	@instrument_tool(mt.name)
	def _run(args: Dict[str, Any]) -> Dict[str, Any]:
		kwargs = args if isinstance(args, dict) else {}
		if is_async:
			# Execute coroutine in a fresh event loop within thread worker
			res = asyncio.run(fn(**kwargs))
		else:
			res = fn(**kwargs)
		if isinstance(res, dict):
			return res
		return {"result": res}
	return ToolSpec(name=mt.name, input_model=mt.input_model, run=_run)