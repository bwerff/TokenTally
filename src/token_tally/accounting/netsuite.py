"""Simple NetSuite integration helpers."""

from __future__ import annotations

import base64
import json
import os
import urllib.request


def push_invoice(invoice: dict) -> dict:
    """Push a single invoice to NetSuite and return the response.

    The NetSuite API credentials and endpoint are taken from the following
    environment variables:

    ``NETSUITE_ACCOUNT`` - account ID
    ``NETSUITE_TOKEN``   - API token
    ``NETSUITE_SECRET``  - API secret
    ``NETSUITE_API_URL`` - base URL for invoice POSTs
    """

    account = os.getenv("NETSUITE_ACCOUNT")
    token = os.getenv("NETSUITE_TOKEN")
    secret = os.getenv("NETSUITE_SECRET")
    url = os.getenv("NETSUITE_API_URL", "https://api.netsuite.com/invoices")
    if not all([account, token, secret]):
        raise ValueError("Missing NetSuite credentials")

    data = json.dumps(invoice).encode()
    req = urllib.request.Request(url, data=data)
    auth = base64.b64encode(f"{account}:{token}:{secret}".encode()).decode()
    req.add_header("Authorization", f"Basic {auth}")
    req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())
