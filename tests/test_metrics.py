import sys
import pathlib
import threading
from urllib.request import urlopen

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from token_tally.metrics import REQUEST_COUNTER, TOKEN_COUNTER
from token_tally.token_counter import count_local_tokens
from token_tally.server import MarkupHandler
from http.server import HTTPServer


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
