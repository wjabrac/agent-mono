from typing import Any, Callable, Dict, List, Optional, get_type_hints
from pydantic import BaseModel, Field, create_model
from core.tools.registry import ToolSpec
from core.instrumentation import instrument_tool


class MicrotoolSpec(BaseModel):
    name: str
    description: str = ""
    tags: List[str] = Field(default_factory=list)
    input_model: Optional[type[BaseModel]] = None


def microtool(
    name: str,
    *,
    description: str = "",
    tags: List[str] | None = None,
    input_model: Optional[type[BaseModel]] = None,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    def decorator(fn: Callable[..., Any]) -> Callable[..., Any]:
        model = input_model
        if model is None:
            import inspect

            hints = get_type_hints(fn)
            sig = inspect.signature(fn)
            fields: Dict[str, tuple[Any, Any]] = {}
            for param_name, param in sig.parameters.items():
                if param.kind in (
                    inspect.Parameter.VAR_POSITIONAL,
                    inspect.Parameter.VAR_KEYWORD,
                ):
                    continue
                ann = hints.get(param_name, Any)
                default = param.default if param.default is not inspect._empty else ...
                fields[param_name] = (ann, default)
            if fields:
                model = create_model(f"{fn.__name__.title()}Input", **fields)  # type: ignore
        mt_spec = MicrotoolSpec(name=name, description=description, tags=tags or [], input_model=model)
        setattr(fn, "_microtool_spec", mt_spec)
        # Defer manifest entry until discovery so file path is known
        return fn

    return decorator


def build_toolspec_from_microtool(fn: Callable[..., Any]) -> ToolSpec:
    import inspect

    mt: MicrotoolSpec = getattr(fn, "_microtool_spec")
    model = mt.input_model
    if inspect.iscoroutinefunction(fn):

        @instrument_tool(mt.name)
        async def _run(args: Dict[str, Any]) -> Dict[str, Any]:
            kwargs = model(**(args or {})).model_dump() if model else (args or {})
            res = await fn(**kwargs)
            return res if isinstance(res, dict) else {"result": res}

    else:

        @instrument_tool(mt.name)
        def _run(args: Dict[str, Any]) -> Dict[str, Any]:
            kwargs = model(**(args or {})).model_dump() if model else (args or {})
            res = fn(**kwargs)
            return res if isinstance(res, dict) else {"result": res}

    return ToolSpec(name=mt.name, input_model=model, run=_run)
