from __future__ import annotations

import argparse
import time
from typing import Sequence
from urllib.request import urlopen
from urllib.error import URLError

from .audit import AuditLog


def verify_audit_log(db_path: str) -> bool:
    """Return ``True`` if the audit log hash chain is intact."""
    log = AuditLog(db_path)
    return log.verify_chain()


def check_health(url: str, timeout: float = 5.0) -> bool:
    """Return ``True`` if ``url`` responds with HTTP 200."""
    try:
        with urlopen(url, timeout=timeout) as resp:
            return resp.status == 200
    except Exception:
        return False


def run(
    db_path: str,
    health_urls: Sequence[str],
    interval: int = 300,
    iterations: int | None = None,
) -> None:
    """Periodically verify audit log and service health."""
    count = 0
    while True:
        if not verify_audit_log(db_path):
            print("Audit log verification failed", flush=True)
        for url in health_urls:
            if not check_health(url):
                print(f"Health check failed for {url}", flush=True)
        count += 1
        if iterations is not None and count >= iterations:
            break
        time.sleep(interval)


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="SOC2 monitoring loop")
    parser.add_argument("db_path", help="Path to audit log database")
    parser.add_argument("health_urls", nargs="*", help="URLs to check")
    parser.add_argument(
        "--interval", type=int, default=300, help="Seconds between checks"
    )
    args = parser.parse_args(list(argv) if argv is not None else None)
    run(args.db_path, args.health_urls, args.interval)


if __name__ == "__main__":
    main(None)

__all__ = ["verify_audit_log", "check_health", "run", "main"]
