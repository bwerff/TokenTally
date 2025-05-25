from __future__ import annotations

import argparse
import json
import time
import hmac
import hashlib
from http.server import BaseHTTPRequestHandler, HTTPServer

from .ledger import Ledger


class StripeWebhookHandler(BaseHTTPRequestHandler):
    """Handle Stripe webhook events and update ledger status."""

    secret: str = ""
    ledger = Ledger()

    def _send_json(self, data: dict, status: int = 200) -> None:
        body = json.dumps(data).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    @classmethod
    def verify_signature(cls, payload: bytes, header: str) -> bool:
        """Return ``True`` if ``header`` matches the HMAC of ``payload``."""
        try:
            parts = dict(item.split("=", 1) for item in header.split(","))
        except ValueError:
            return False
        timestamp = parts.get("t")
        signature = parts.get("v1")
        if not timestamp or not signature:
            return False
        try:
            ts = int(timestamp)
        except ValueError:
            return False
        if abs(time.time() - ts) > 300:
            return False
        expected = hmac.new(
            cls.secret.encode(),
            msg=f"{timestamp}.".encode() + payload,
            digestmod=hashlib.sha256,
        ).hexdigest()
        return hmac.compare_digest(expected, signature)

    def do_POST(self) -> None:  # pragma: no cover - delegated to tests
        if self.path != "/webhook":
            self._send_json({"error": "not found"}, 404)
            return
        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length)
        sig = self.headers.get("Stripe-Signature", "")
        if not self.verify_signature(body, sig):
            self._send_json({"error": "invalid signature"}, 400)
            return
        event = json.loads(body)
        obj = event.get("data", {}).get("object", {})
        status = obj.get("status")
        record_id = obj.get("id")
        if record_id and status:
            self.ledger.update_status(record_id, status)
        self._send_json({"status": "ok"})


def run(
    secret: str, db_path: str = "ledger.db", host: str = "0.0.0.0", port: int = 8080
) -> None:
    """Run a simple HTTP server to process Stripe webhooks."""
    handler = type(
        "Handler",
        (StripeWebhookHandler,),
        {"secret": secret, "ledger": Ledger(db_path)},
    )
    server = HTTPServer((host, port), handler)
    print(f"Stripe webhook server running on {host}:{port}")
    server.serve_forever()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Stripe webhook server")
    parser.add_argument("secret", help="Webhook signing secret")
    parser.add_argument("--db-path", default="ledger.db", help="Path to ledger.db")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8080)
    args = parser.parse_args()
    run(args.secret, db_path=args.db_path, host=args.host, port=args.port)
