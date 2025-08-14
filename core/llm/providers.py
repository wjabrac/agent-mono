"""LLM provider implementations.

This module defines a small provider abstraction that allows the rest of the
codebase to talk to language models without depending on any specific vendor
SDK.  Providers are expected to expose two core capabilities:

``generate(prompt, **kwargs)`` – produce text given a prompt.
``count_tokens(text)`` – utility used for budgeting requests.

Implementations included here cover both hosted models (OpenAI) and local /
free models via HuggingFace transformers.  All providers emit lightweight
in-process metrics and trace events so they are observable in production
without requiring a Prometheus server.
"""

from __future__ import annotations

import os
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from core.observability.metrics import llm_calls_total, llm_latency_ms
from core.observability.trace import log_event, start_trace
from core.trace_context import (
    current_tags,
    current_thread_id,
    current_trace_id,
)


class BaseLLMProvider(ABC):
    """Base interface for all LLM providers."""

    model_name: str

    @abstractmethod
    def generate(self, prompt: str, **kwargs: Any) -> str:
        """Generate text from ``prompt``.

        Sub-classes should raise exceptions as normal – the caller is
        responsible for handling them.  Implementations provided here will
        emit metrics and tracing information for observability.
        """

    @abstractmethod
    def count_tokens(self, text: str) -> int:
        """Return the token count for ``text``."""

    # ------------------------------------------------------------------
    # Helper methods used by subclasses
    def _log_start(self, prompt: str, kwargs: Dict[str, Any]) -> str:
        thread_id = current_thread_id.get()
        trace_id = current_trace_id.get()
        tags = current_tags.get()
        if not trace_id:
            trace_id = start_trace(thread_id)
        log_event(
            trace_id,
            "decision",
            "llm:start",
            {"model": self.model_name, "prompt": prompt, "tags": tags, **kwargs},
        )
        return trace_id

    def _log_end(
        self, trace_id: str, ok: bool, start: float, payload: Optional[Dict[str, Any]] = None
    ) -> None:
        tags = current_tags.get()
        tag_str = ",".join(tags) if tags else ""
        llm_calls_total.labels(self.model_name, str(ok).lower(), tag_str).inc()
        llm_latency_ms.labels(self.model_name, tag_str).observe((time.time() - start) * 1000.0)
        log_event(
            trace_id,
            "decision",
            "llm:done" if ok else "llm:error",
            {
                "model": self.model_name,
                "ms": int((time.time() - start) * 1000),
                "ok": ok,
                "tags": tags,
                **(payload or {}),
            },
        )


# ----------------------------------------------------------------------
# OpenAI provider


class OpenAIProvider(BaseLLMProvider):
    """Provider that calls the OpenAI chat completion API."""

    def __init__(self, model: Optional[str] = None, api_key: Optional[str] = None):
        self.model_name = model or os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
        self._api_key = api_key or os.getenv("OPENAI_API_KEY")
        # Import lazily so environments without the dependency can still use
        # other providers.
        try:
            from openai import OpenAI  # type: ignore

            self._client = OpenAI(api_key=self._api_key)
        except Exception:  # pragma: no cover - handled at runtime
            self._client = None

    # Resilient generate with simple retry logic
    def generate(self, prompt: str, **kwargs: Any) -> str:  # pragma: no cover - network call
        if self._client is None:
            raise RuntimeError("openai package is required for OpenAIProvider")

        trace_id = self._log_start(prompt, kwargs)
        start = time.time()
        last_err: Optional[Exception] = None
        for _ in range(kwargs.pop("retries", 2) + 1):
            try:
                resp = self._client.chat.completions.create(
                    model=self.model_name,
                    messages=[{"role": "user", "content": prompt}],
                    **kwargs,
                )
                text = resp.choices[0].message.content  # type: ignore[attr-defined]
                self._log_end(trace_id, True, start, {"response": text})
                return text
            except Exception as e:
                last_err = e
        # All retries failed
        self._log_end(trace_id, False, start, {"error": str(last_err)})
        raise last_err  # type: ignore

    def count_tokens(self, text: str) -> int:
        try:  # pragma: no cover - best effort
            import tiktoken

            enc = tiktoken.encoding_for_model(self.model_name)
            return len(enc.encode(text))
        except Exception:
            return len(text.split())


# ----------------------------------------------------------------------
# Local HuggingFace provider


class LocalHFProvider(BaseLLMProvider):
    """Provider running a local HuggingFace transformer model.

    This uses a tiny model by default so that unit tests remain light-weight.
    The model is loaded lazily on first use.
    """

    def __init__(self, model_name: Optional[str] = None, device: Optional[str] = None):
        self.model_name = model_name or os.getenv("HF_MODEL", "sshleifer/tiny-gpt2")
        self.device = device
        self._model = None
        self._tokenizer = None

    # Lazy initialisation
    def _ensure_loaded(self) -> None:  # pragma: no cover - heavy import
        if self._model is not None:
            return
        from transformers import AutoModelForCausalLM, AutoTokenizer
        import torch

        self._tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self._model = AutoModelForCausalLM.from_pretrained(self.model_name)
        dev = self.device or ("cuda" if torch.cuda.is_available() else "cpu")
        self._model.to(dev)

    def generate(self, prompt: str, **kwargs: Any) -> str:  # pragma: no cover - heavy
        self._ensure_loaded()
        assert self._model is not None and self._tokenizer is not None

        trace_id = self._log_start(prompt, kwargs)
        start = time.time()
        inputs = self._tokenizer(prompt, return_tensors="pt").to(self._model.device)  # type: ignore
        output_ids = self._model.generate(**inputs, **kwargs)
        text = self._tokenizer.decode(output_ids[0], skip_special_tokens=True)
        self._log_end(trace_id, True, start, {"response": text})
        return text

    def count_tokens(self, text: str) -> int:
        self._ensure_loaded()
        assert self._tokenizer is not None
        return len(self._tokenizer.encode(text))


# ----------------------------------------------------------------------
# GPT4All provider


class GPT4AllProvider(BaseLLMProvider):
    """Provider using a local GPT4All quantized model."""

    def __init__(self, model_name: Optional[str] = None, model_path: Optional[str] = None):
        self.model_name = model_name or os.getenv("GPT4ALL_MODEL", "gpt4all-falcon-q4_0.bin")
        self.model_path = os.path.expanduser(model_path or os.getenv("GPT4ALL_MODEL_PATH", "~/.cache/gpt4all"))
        self._model = None

    def _ensure_loaded(self) -> None:  # pragma: no cover - heavy import
        if self._model is not None:
            return
        from gpt4all import GPT4All  # type: ignore

        self._model = GPT4All(self.model_name, model_path=self.model_path, allow_download=False)

    def generate(self, prompt: str, **kwargs: Any) -> str:  # pragma: no cover - heavy
        self._ensure_loaded()
        trace_id = self._log_start(prompt, kwargs)
        start = time.time()
        text = self._model.generate(prompt, **kwargs)  # type: ignore[attr-defined]
        self._log_end(trace_id, True, start, {"response": text})
        return text

    def count_tokens(self, text: str) -> int:
        return len(text.split())


__all__ = [
    "BaseLLMProvider",
    "OpenAIProvider",
    "LocalHFProvider",
    "GPT4AllProvider",
]

