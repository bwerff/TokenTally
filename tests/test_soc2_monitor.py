import sys
import pathlib
import sqlite3
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from token_tally.audit import AuditLog
from token_tally.soc2_monitor import verify_audit_log, check_health, run


class _OKHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        self.send_response(200)
        self.end_headers()


class _FailHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        self.send_response(500)
        self.end_headers()


def _start_server(handler) -> tuple[HTTPServer, threading.Thread, int]:
    server = HTTPServer(("localhost", 0), handler)
    thread = threading.Thread(target=server.serve_forever)
    thread.daemon = True
    thread.start()
    return server, thread, server.server_address[1]


def test_verify_audit_log(tmp_path):
    db = tmp_path / "audit.db"
    log = AuditLog(str(db))
    log.add_event("e1", "c1", "foo", 1)
    log.add_event("e2", "c1", "bar", 2)
    assert verify_audit_log(str(db))

    with sqlite3.connect(db) as conn:
        conn.execute("UPDATE audit_events SET prev_hash = 'bad' WHERE event_id = 'e2'")
        conn.commit()

    assert not verify_audit_log(str(db))


def test_check_health_ok_and_fail():
    server, thread, port = _start_server(_OKHandler)
    try:
        assert check_health(f"http://localhost:{port}")
    finally:
        server.shutdown()
        thread.join()

    # After shutdown the check should fail
    assert not check_health(f"http://localhost:{port}")


def test_run_single_iteration(tmp_path):
    db = tmp_path / "audit.db"
    log = AuditLog(str(db))
    log.add_event("e1", "c1", "foo", 1)
    server, thread, port = _start_server(_OKHandler)
    try:
        run(str(db), [f"http://localhost:{port}"], interval=0, iterations=1)
    finally:
        server.shutdown()
        thread.join()
