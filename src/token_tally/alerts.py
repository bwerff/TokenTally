"""Utility functions for sending webhook alerts."""

from __future__ import annotations

import json
import urllib.request


def send_webhook_message(url: str, message: str) -> None:
    """POST a simple JSON payload to the given webhook URL."""
    data = json.dumps({"text": message}).encode()
    req = urllib.request.Request(url, data=data)
    req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req) as resp:  # pragma: no cover - network
        resp.read()
