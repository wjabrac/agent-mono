import os
from typing import Any, Dict, Optional

try:
    import httpx  # type: ignore
except Exception:  # pragma: no cover - optional dep
    httpx = None  # type: ignore

from pydantic import BaseModel
from core.tools.registry import ToolSpec
from core.instrumentation import instrument_tool


class RemoteToolConfig(BaseModel):
    name: str
    url: str
    method: str = "POST"
    api_key_env: Optional[str] = None
    timeout_s: int = 20
    result_path: Optional[str] = None  # dot path to extract value


def _remote_runner(config: RemoteToolConfig):
    @instrument_tool(config.name)
    def _run(args: Dict[str, Any]) -> Dict[str, Any]:
        if httpx is None:
            raise RuntimeError("httpx_not_installed")
        headers: Dict[str, str] = {"Content-Type": "application/json"}
        if config.api_key_env and os.getenv(config.api_key_env):
            headers["Authorization"] = f"Bearer {os.getenv(config.api_key_env)}"
        req = {"url": config.url, "headers": headers, "timeout": config.timeout_s}
        if config.method.upper() == "GET":
            resp = httpx.get(**req, params=args)
        else:
            resp = httpx.post(**req, json=args)
        resp.raise_for_status()
        data = resp.json()
        if config.result_path:
            # naive dot path
            val = data
            for part in config.result_path.split("."):
                if isinstance(val, dict):
                    val = val.get(part)
            data = val
        return {"result": data}
    return _run


def build_remote_tool(config: RemoteToolConfig) -> ToolSpec:
    return ToolSpec(name=config.name, input_model=None, run=_remote_runner(config))