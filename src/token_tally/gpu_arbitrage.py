"""Helpers for selecting the cheapest GPU host."""

from __future__ import annotations

import json
import os
from urllib.request import urlopen


def choose_best_gpu_host(feed_url: str | None = None) -> str:
    """Return the host with the lowest spot price."""
    feed_url = feed_url or os.getenv("GPU_SPOT_FEED")
    if not feed_url:
        raise ValueError("feed_url must be provided")
    with urlopen(feed_url) as resp:
        data = json.loads(resp.read().decode())
    if not isinstance(data, dict) or not data:
        raise ValueError("invalid price feed")
    host = min(data.items(), key=lambda item: item[1])[0]
    return host


__all__ = ["choose_best_gpu_host"]
