from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import os
from io import BytesIO
from pathlib import Path
import cgi

from .processor import ReceiptProcessor

DATA_DIR = Path(__file__).resolve().parent / "data"
DATA_DIR.mkdir(exist_ok=True)

processor = ReceiptProcessor(DATA_DIR)


class ReceiptHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path != "/upload":
            self.send_error(404)
            return
        content_type = self.headers.get('Content-Type')
        if not content_type:
            self.send_error(400, "Missing Content-Type")
            return
        ctype, pdict = cgi.parse_header(content_type)
        if ctype != 'multipart/form-data':
            self.send_error(400, "Expected multipart form data")
            return
        pdict['boundary'] = bytes(pdict['boundary'], "utf-8")
        pdict['CONTENT-LENGTH'] = int(self.headers.get('Content-Length'))
        form = cgi.FieldStorage(fp=self.rfile, headers=self.headers, environ={'REQUEST_METHOD':'POST'}, keep_blank_values=True)
        file_item = form['file'] if 'file' in form else None
        if file_item is None or not file_item.file:
            self.send_error(400, "No file uploaded")
            return
        tmp_path = DATA_DIR / file_item.filename
        with open(tmp_path, 'wb') as f:
            f.write(file_item.file.read())
        results = processor.process_receipt(tmp_path)
        response = json.dumps(results).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(response)))
        self.end_headers()
        self.wfile.write(response)
        os.remove(tmp_path)


def run(host: str = "0.0.0.0", port: int = 8080):
    server = HTTPServer((host, port), ReceiptHandler)
    print(f"ReceiptProcessor service running on {host}:{port}")
    server.serve_forever()


if __name__ == "__main__":
    run()
