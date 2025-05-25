import argparse
from typing import Iterable

from .billing import BillingService
from .ledger import Ledger


def main(argv: Iterable[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Billing utilities")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sync_p = sub.add_parser("sync", help="Sync usage events to Stripe")
    sync_p.add_argument("db_path", help="Path to ledger.db")
    sync_p.add_argument("api_key", help="Stripe API key")
    args = parser.parse_args(list(argv) if argv is not None else None)

    if args.cmd == "sync":
        service = BillingService(args.api_key, Ledger(args.db_path))
        count = service.sync_usage_events()
        print(count)


def cli() -> None:
    main()


if __name__ == "__main__":
    cli()
