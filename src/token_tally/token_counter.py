"""Token counting utilities for multiple model providers.

Vendor tokenisers are used when available to provide accurate counts. If the
optional libraries are missing, we fall back to a simple regex-based
approximation so the helpers remain dependency-free.
"""

from __future__ import annotations

import re

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
    if _openai_encoding is not None:
        try:
            return len(_openai_encoding.encode(text))
        except Exception:  # pragma: no cover - defensive
            pass
    return len(_regex_split(text))


def count_anthropic_tokens(text: str) -> int:
    """Token count for Anthropic models using ``anthropic`` when available."""
    if _anthropic_count_tokens is not None:
        try:
            return _anthropic_count_tokens(text)
        except Exception:  # pragma: no cover - defensive
            pass
    return len(_regex_split(text))


def count_local_tokens(text: str) -> int:
    """Token count for local models using a simple whitespace split."""
    return len(text.split())


_PROVIDER_MAP = {
    "openai": count_openai_tokens,
    "anthropic": count_anthropic_tokens,
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
    "count_local_tokens",
    "count_tokens",
]
