import os
import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import sys
import pathlib

# add src to path
sys.path.append(str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from token_tally.accounting import netsuite


class _Handler(BaseHTTPRequestHandler):
    received = {}

    def do_POST(self):
        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length)
        _Handler.received["body"] = json.loads(body)
        _Handler.received["auth"] = self.headers.get("Authorization")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(b'{"status": "ok"}')


def _start_server():
    server = HTTPServer(("127.0.0.1", 0), _Handler)
    t = threading.Thread(target=server.serve_forever)
    t.daemon = True
    t.start()
    return server, t


def test_push_invoice_env(monkeypatch):
    server, thread = _start_server()
    url = f"http://127.0.0.1:{server.server_address[1]}/push"
    monkeypatch.setenv("NETSUITE_ACCOUNT", "acct")
    monkeypatch.setenv("NETSUITE_TOKEN", "tok")
    monkeypatch.setenv("NETSUITE_SECRET", "sec")
    monkeypatch.setenv("NETSUITE_API_URL", url)

    resp = netsuite.push_invoice({"id": "inv1", "total": 10})

    server.shutdown()
    thread.join()

    assert resp["status"] == "ok"
    assert _Handler.received["body"]["id"] == "inv1"
    assert _Handler.received["auth"].startswith("Basic ")
