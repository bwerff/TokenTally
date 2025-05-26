"""Provider base URL routing with GPU spot-price support."""

from __future__ import annotations

import os

from .gpu_arbitrage import choose_best_gpu_host

PROVIDER_BASE = {
    "openai": os.environ.get("OPENAI_BASE", "https://api.openai.com/v1"),
    "anthropic": os.environ.get("ANTHROPIC_BASE", "https://api.anthropic.com"),
    "cohere": os.environ.get("COHERE_BASE", "https://api.cohere.ai"),
}


def route_provider(provider: str, model: str | None = None) -> str:
    """Return the base URL for ``provider``.

    ``local``/``ollama`` providers route to the cheapest GPU host.
    """
    key = provider.lower()
    if key in {"local", "ollama"}:
        return choose_best_gpu_host()
    base = PROVIDER_BASE.get(key)
    if base is None:
        raise ValueError(f"unknown provider: {provider}")
    return base


__all__ = ["route_provider"]
