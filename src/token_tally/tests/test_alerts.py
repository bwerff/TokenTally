import sys
import pathlib

sys.path.append(str(pathlib.Path(__file__).resolve().parents[2]))

import types

from token_tally.alerts import send_webhook_message


class DummyResp:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        pass

    def read(self):
        return b"ok"


def test_send_webhook_message(monkeypatch):
    called = {}

    def fake_urlopen(req):
        called["url"] = req.full_url
        called["data"] = req.data
        return DummyResp()

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    send_webhook_message("http://example.com", "hi")
    assert called["url"] == "http://example.com"
    assert b"hi" in called["data"]
