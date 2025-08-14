"""Factory for selecting an LLM provider.

Usage::

    from core.llm import get_provider
    provider = get_provider()
    text = provider.generate("hello world")

The provider chosen is based on the ``LLM_PROVIDER`` environment variable or a
configuration dictionary passed to :func:`get_provider`.
"""

from __future__ import annotations

import os
from typing import Dict, Optional

from .providers import BaseLLMProvider, LocalHFProvider, OpenAIProvider, GPT4AllProvider

_PROVIDER: Optional[BaseLLMProvider] = None


def get_provider(config: Optional[Dict[str, str]] = None) -> BaseLLMProvider:
    """Return a singleton instance of :class:`BaseLLMProvider`.

    Parameters
    ----------
    config:
        Optional configuration dictionary.  Recognised keys include
        ``provider`` and ``model``.
    """

    global _PROVIDER
    if _PROVIDER is not None:
        return _PROVIDER

    cfg = config or {}
    provider_name = cfg.get("provider") or os.getenv("LLM_PROVIDER", "local")
    model = cfg.get("model") or os.getenv("LLM_MODEL")

    if provider_name.lower() in {"openai", "gpt", "chatgpt"}:
        _PROVIDER = OpenAIProvider(model=model)
    elif provider_name.lower() in {"local", "hf", "huggingface"}:
        _PROVIDER = LocalHFProvider(model_name=model)
    elif provider_name.lower() in {"gpt4all", "gpt4a"}:
        _PROVIDER = GPT4AllProvider(model_name=model)
    else:  # pragma: no cover - unexpected config
        raise ValueError(f"Unknown LLM provider: {provider_name}")

    return _PROVIDER


__all__ = [
    "BaseLLMProvider",
    "OpenAIProvider",
    "LocalHFProvider",
    "GPT4AllProvider",
    "get_provider",
]

