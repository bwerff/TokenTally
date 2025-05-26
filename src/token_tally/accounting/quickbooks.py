"""QuickBooks API helpers."""

from __future__ import annotations

import json
import urllib.request

QUICKBOOKS_API_URL = "https://quickbooks.api.intuit.com/v3/invoices"


def send_invoice_to_quickbooks(invoice: dict, token: str) -> dict:
    """Post ``invoice`` to the QuickBooks API using ``token``."""
    data = json.dumps(invoice).encode()
    req = urllib.request.Request(QUICKBOOKS_API_URL, data=data)
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())
