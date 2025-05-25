"""Simple Prometheus metrics helpers."""

from __future__ import annotations

try:
    from prometheus_client import Counter, start_http_server

    _PROM_AVAILABLE = True
except Exception:  # pragma: no cover - prometheus optional
    _PROM_AVAILABLE = False

    class Counter:  # type: ignore
        def __init__(self, *args, **kwargs) -> None:
            self.value = 0.0
            self._value = self

        def inc(self, amount: float = 1.0) -> None:
            self.value += amount

        def get(self) -> float:
            return self.value

    def start_http_server(*args, **kwargs) -> None:  # type: ignore
        print("prometheus_client not installed; metrics disabled")


REQUEST_COUNTER = Counter("requests_handled_total", "Number of HTTP requests handled")
TOKEN_COUNTER = Counter("tokens_counted_total", "Number of tokens counted")


def start_metrics_server(port: int = 8001) -> None:
    """Expose metrics on an HTTP port for Prometheus scraping."""
    if _PROM_AVAILABLE:
        start_http_server(port)
    else:  # pragma: no cover - no prometheus
        start_http_server(port)
