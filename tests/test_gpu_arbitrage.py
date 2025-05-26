import sys
import pathlib

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from token_tally import gpu_arbitrage, cost_router


class DummyResp:
    def __init__(self, data: bytes):
        self.data = data

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        pass

    def read(self) -> bytes:
        return self.data


def test_choose_best_gpu_host(monkeypatch):
    data = b'{"h1": 0.5, "h2": 0.3}'
    monkeypatch.setattr(gpu_arbitrage, "urlopen", lambda url: DummyResp(data))
    host = gpu_arbitrage.choose_best_gpu_host("http://feed")
    assert host == "h2"


def test_cost_router_local(monkeypatch):
    monkeypatch.setattr(cost_router, "choose_best_gpu_host", lambda: "best")
    base = cost_router.route_provider("local")
    assert base == "best"
