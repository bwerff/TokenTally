import sys
import pathlib
import threading
from urllib.request import urlopen

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from token_tally.metrics import REQUEST_COUNTER, TOKEN_COUNTER
from token_tally.token_counter import count_local_tokens
from token_tally.server import MarkupHandler
from http.server import HTTPServer
import subprocess
import json
from pathlib import Path


def test_token_counter_metric():
    before = TOKEN_COUNTER._value.get()
    count_local_tokens("a b c")
    after = TOKEN_COUNTER._value.get()
    assert after - before == 3


def test_request_metric_increment():
    server = HTTPServer(("localhost", 0), MarkupHandler)
    thread = threading.Thread(target=server.serve_forever)
    thread.daemon = True
    thread.start()
    port = server.server_address[1]
    before = REQUEST_COUNTER._value.get()
    urlopen(f"http://localhost:{port}/markup-rules").read()
    server.shutdown()
    thread.join()
    after = REQUEST_COUNTER._value.get()
    assert after - before == 1


def test_gateway_latency_metrics(tmp_path):
    ts_dir = Path(__file__).resolve().parents[1] / "gateway-worker" / "src"
    out_dir = tmp_path
    subprocess.run(
        [
            "tsc",
            str(ts_dir / "metrics.ts"),
            "--target",
            "ES2020",
            "--module",
            "commonjs",
            "--outDir",
            str(out_dir),
        ],
        check=True,
    )
    run_js = out_dir / "run.js"
    run_js.write_text(
        "const m = require('./metrics.js');"
        "m.recordLatency('openai', 40);"
        "m.recordLatency('openai', 60);"
        "console.log(m.metricsText());"
    )
    result = subprocess.run(
        ["node", str(run_js)], capture_output=True, text=True, check=True
    )
    assert 'gateway_request_latency_ms_total{provider="openai"} 100' in result.stdout
