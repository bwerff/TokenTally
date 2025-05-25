import json
import uuid
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse

from .markup import MarkupRuleStore
from .metrics import REQUEST_COUNTER, start_metrics_server

try:
    from opentelemetry import trace
except Exception:  # pragma: no cover - optional

    class _DummySpan:
        def __enter__(self):
            return self

        def __exit__(self, *exc: object) -> None:
            pass

        def set_attribute(self, *args: object, **kwargs: object) -> None:
            pass

    class _DummyTracer:
        def start_as_current_span(self, name: str) -> _DummySpan:
            return _DummySpan()

    class _TraceModule:
        def get_tracer(self, name: str | None = None) -> _DummyTracer:
            return _DummyTracer()

    trace = _TraceModule()  # type: ignore

tracer = trace.get_tracer(__name__)

store = MarkupRuleStore()


class MarkupHandler(BaseHTTPRequestHandler):
    def _send_json(self, data, status=200):
        body = json.dumps(data).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        REQUEST_COUNTER.inc()
        with tracer.start_as_current_span("MarkupHandler.do_GET"):
            path = urlparse(self.path).path
            if path == "/markup-rules":
                self._send_json(store.list_rules())
            elif path.startswith("/markup-rules/"):
                rule_id = path.split("/")[-1]
                rule = store.get_rule(rule_id)
                if rule:
                    self._send_json(rule)
                else:
                    self._send_json({"error": "not found"}, 404)
            else:
                self._send_json({"error": "not found"}, 404)

    def do_POST(self):
        REQUEST_COUNTER.inc()
        with tracer.start_as_current_span("MarkupHandler.do_POST"):
            path = urlparse(self.path).path
            if path != "/markup-rules":
                self._send_json({"error": "not found"}, 404)
                return
            length = int(self.headers.get("Content-Length", "0"))
            body = json.loads(self.rfile.read(length)) if length else {}
            rule_id = body.get("id") or str(uuid.uuid4())
            provider = body.get("provider")
            model = body.get("model")
            markup = body.get("markup")
            effective_date = body.get("effective_date")
            if not all([provider, model, markup, effective_date]):
                self._send_json({"error": "invalid body"}, 400)
                return
            store.create_rule(rule_id, provider, model, float(markup), effective_date)
            self._send_json({"id": rule_id})

    def do_PUT(self):
        REQUEST_COUNTER.inc()
        with tracer.start_as_current_span("MarkupHandler.do_PUT"):
            path = urlparse(self.path).path
            if not path.startswith("/markup-rules/"):
                self._send_json({"error": "not found"}, 404)
                return
            rule_id = path.split("/")[-1]
            length = int(self.headers.get("Content-Length", "0"))
            updates = json.loads(self.rfile.read(length)) if length else {}
            store.update_rule(rule_id, **updates)
            self._send_json({"status": "ok"})

    def do_DELETE(self):
        REQUEST_COUNTER.inc()
        with tracer.start_as_current_span("MarkupHandler.do_DELETE"):
            path = urlparse(self.path).path
            if not path.startswith("/markup-rules/"):
                self._send_json({"error": "not found"}, 404)
                return
            rule_id = path.split("/")[-1]
            store.delete_rule(rule_id)
            self._send_json({"status": "deleted"})


def run(host: str = "0.0.0.0", port: int = 8000):
    start_metrics_server()
    server = HTTPServer((host, port), MarkupHandler)
    print(f"Markup server running on {host}:{port}")
    server.serve_forever()


if __name__ == "__main__":
    run()
