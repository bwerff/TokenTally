"""Token counting utilities for multiple model providers.

Vendor tokenisers are used when available to provide accurate counts. If the
optional libraries are missing, we fall back to a simple regex-based
approximation so the helpers remain dependency-free.
"""

from __future__ import annotations

import re
from .metrics import TOKEN_COUNTER

try:
    from opentelemetry import trace
except Exception:  # pragma: no cover - opentelemetry optional

    class _DummySpan:
        def __enter__(self):
            return self

        def __exit__(self, *exc: object) -> None:
            pass

        def set_attribute(self, *args: object, **kwargs: object) -> None:
            pass

    class _DummyTracer:
        def start_as_current_span(self, name: str) -> _DummySpan:
            return _DummySpan()

    class _TraceModule:
        def get_tracer(self, name: str | None = None) -> _DummyTracer:
            return _DummyTracer()

    trace = _TraceModule()  # type: ignore

tracer = trace.get_tracer(__name__)

try:  # Optional; only used if installed
    import tiktoken

    _openai_encoding = tiktoken.get_encoding("cl100k_base")
except Exception:  # pragma: no cover - missing optional dependency
    tiktoken = None
    _openai_encoding = None

try:
    from anthropic import count_tokens as _anthropic_count_tokens
except Exception:  # pragma: no cover - missing optional dependency
    _anthropic_count_tokens = None

_WORD_RE = re.compile(r"\w+|[^\w\s]", re.UNICODE)


def _regex_split(text: str) -> list[str]:
    """Split text into word-like tokens using a regex pattern."""
    return _WORD_RE.findall(text)


def count_openai_tokens(text: str) -> int:
    """Token count for OpenAI models using ``tiktoken`` when available."""
    with tracer.start_as_current_span("count_openai_tokens") as span:
        if _openai_encoding is not None:
            try:
                count = len(_openai_encoding.encode(text))
            except Exception:  # pragma: no cover - defensive
                count = len(_regex_split(text))
        else:
            count = len(_regex_split(text))
        try:
            span.set_attribute("tokens", count)
        except Exception:  # pragma: no cover - span may be dummy
            pass
    TOKEN_COUNTER.inc(count)
    return count


def count_anthropic_tokens(text: str) -> int:
    """Token count for Anthropic models using ``anthropic`` when available."""
    with tracer.start_as_current_span("count_anthropic_tokens") as span:
        if _anthropic_count_tokens is not None:
            try:
                count = _anthropic_count_tokens(text)
            except Exception:  # pragma: no cover - defensive
                count = len(_regex_split(text))
        else:
            count = len(_regex_split(text))
        try:
            span.set_attribute("tokens", count)
        except Exception:  # pragma: no cover - span may be dummy
            pass
    TOKEN_COUNTER.inc(count)
    return count


def count_local_tokens(text: str) -> int:
    """Token count for local models using a simple whitespace split."""
    with tracer.start_as_current_span("count_local_tokens") as span:
        count = len(text.split())
        try:
            span.set_attribute("tokens", count)
        except Exception:  # pragma: no cover - span may be dummy
            pass
    TOKEN_COUNTER.inc(count)
    return count


def count_ollama_tokens(text: str) -> int:
    """Token count for Ollama models using a regex split fallback."""
    with tracer.start_as_current_span("count_ollama_tokens") as span:
        count = len(_regex_split(text))
        try:
            import importlib

            if importlib.util.find_spec("ollama"):
                import ollama  # type: ignore

                tokenize = getattr(ollama, "tokenize", None)
                if callable(tokenize):
                    try:
                        count = len(tokenize(text))
                    except Exception:
                        count = len(_regex_split(text))
        except Exception:  # pragma: no cover - defensive
            count = len(_regex_split(text))

        try:
            span.set_attribute("tokens", count)
        except Exception:  # pragma: no cover - span may be dummy
            pass
    TOKEN_COUNTER.inc(count)
    return count


_PROVIDER_MAP = {
    "openai": count_openai_tokens,
    "anthropic": count_anthropic_tokens,
    "ollama": count_ollama_tokens,
}


def count_tokens(provider: str, text: str) -> int:
    """Count tokens for a given provider name.

    Any unknown provider falls back to the local token counter.
    """
    func = _PROVIDER_MAP.get(provider.lower(), count_local_tokens)
    return func(text)


__all__ = [
    "count_openai_tokens",
    "count_anthropic_tokens",
    "count_ollama_tokens",
    "count_local_tokens",
    "count_tokens",
]
