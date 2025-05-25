import json
import subprocess
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "clients" / "python"))
from token_tally_client import TokenTallyClient


class _Handler(BaseHTTPRequestHandler):
    attempts = 0

    def do_GET(self):
        _Handler.attempts += 1
        if _Handler.attempts < 3:
            self.send_response(500)
            self.end_headers()
            return
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(b'{"result": {"data": [{}]}}')


def _start_server():
    server = HTTPServer(("localhost", 0), _Handler)
    t = threading.Thread(target=server.serve_forever)
    t.daemon = True
    t.start()
    return server


def test_python_client_retries():
    _Handler.attempts = 0
    server = _start_server()
    client = TokenTallyClient(f"http://localhost:{server.server_port}")
    assert client.get_usage() == [{}]
    server.shutdown()


def test_typescript_client_retries(tmp_path):
    _Handler.attempts = 0
    server = _start_server()
    ts_dir = Path(__file__).resolve().parents[1] / "clients" / "typescript"
    out_dir = tmp_path
    subprocess.run(
        [
            "tsc",
            str(ts_dir / "index.ts"),
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
        "const c = require('./index.js');"
        "c.getUsage(process.argv[2]).then(r => {"
        "console.log(JSON.stringify(r));"
        "}).catch(e => { console.error(e); process.exit(1); });"
    )
    result = subprocess.run(
        ["node", str(run_js), f"http://localhost:{server.server_port}"],
        capture_output=True,
        text=True,
        check=True,
    )
    assert json.loads(result.stdout.strip()) == [{}]
    server.shutdown()


def test_go_client_retries(tmp_path):
    _Handler.attempts = 0
    server = _start_server()
    go_dir = Path(__file__).resolve().parents[1] / "clients" / "go"
    client_copy = tmp_path / "client.go"
    client_src = (go_dir / "client.go").read_text()
    client_copy.write_text(client_src.replace("package tokentally", "package main"))
    main_go = tmp_path / "main.go"
    main_go.write_text(
        (
            'package main\nimport (\n    "encoding/json"\n    "os"\n)\n'
            "func main() {\n"
            f'    data, err := GetUsage("http://localhost:{server.server_port}")\n'
            "    if err != nil { panic(err) }\n"
            "    json.NewEncoder(os.Stdout).Encode(data)\n"
            "}\n"
        )
    )
    result = subprocess.run(
        ["go", "run", str(main_go), str(client_copy)],
        capture_output=True,
        text=True,
        check=True,
    )
    assert json.loads(result.stdout.strip()) == [{}]
    server.shutdown()
