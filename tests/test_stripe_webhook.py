import sys
import pathlib
import json
import threading
import time
import hmac
import hashlib
import http.client
from http.server import HTTPServer

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from token_tally.stripe_webhook import StripeWebhookHandler
from token_tally.ledger import Ledger


def start_server(tmpdir, secret):
    ledger = Ledger(str(tmpdir / "ledger.db"))
    handler = type(
        "Handler",
        (StripeWebhookHandler,),
        {"secret": secret, "ledger": ledger},
    )
    server = HTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever)
    thread.daemon = True
    thread.start()
    return server, ledger, thread


def sign_payload(secret, payload):
    ts = str(int(time.time()))
    signed = hmac.new(
        secret.encode(),
        msg=f"{ts}.".encode() + payload,
        digestmod=hashlib.sha256,
    ).hexdigest()
    return f"t={ts},v1={signed}"


def test_webhook_updates_status(tmp_path):
    secret = "whsec_test"
    server, ledger, thread = start_server(tmp_path, secret)
    port = server.server_address[1]
    ledger.add_payout("po_1", "u1", 100, "USD", "pending", "stripe")
    event = {
        "type": "payout.paid",
        "data": {"object": {"id": "po_1", "status": "paid"}},
    }
    body = json.dumps(event).encode()
    sig = sign_payload(secret, body)
    conn = http.client.HTTPConnection("127.0.0.1", port)
    conn.request("POST", "/webhook", body, {"Stripe-Signature": sig})
    resp = conn.getresponse()
    assert resp.status == 200
    resp.read()
    conn.close()
    server.shutdown()
    thread.join()
    assert ledger.get_payout("po_1")["status"] == "paid"


def test_invalid_signature(tmp_path):
    secret = "whsec_test"
    server, ledger, thread = start_server(tmp_path, secret)
    port = server.server_address[1]
    event = {
        "type": "payout.paid",
        "data": {"object": {"id": "po_2", "status": "paid"}},
    }
    body = json.dumps(event).encode()
    conn = http.client.HTTPConnection("127.0.0.1", port)
    conn.request("POST", "/webhook", body, {"Stripe-Signature": "t=1,v1=bad"})
    resp = conn.getresponse()
    assert resp.status == 400
    resp.read()
    conn.close()
    server.shutdown()
    thread.join()
