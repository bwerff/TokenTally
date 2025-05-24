"""Token counting utilities for multiple model providers.

This module avoids heavy dependencies by using simple regex-based tokenisation.
It is not a drop-in replacement for vendor tokenisers but provides a reasonable
approximation suitable for metering.
"""

from __future__ import annotations

import re
from typing import Iterable

_WORD_RE = re.compile(r"\w+|[^\w\s]", re.UNICODE)


def _regex_split(text: str) -> list[str]:
    """Split text into word-like tokens using a regex pattern."""
    return _WORD_RE.findall(text)


def count_openai_tokens(text: str) -> int:
    """Approximate token count for OpenAI models."""
    return len(_regex_split(text))


def count_anthropic_tokens(text: str) -> int:
    """Approximate token count for Anthropic models."""
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
