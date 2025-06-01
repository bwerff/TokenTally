import argparse
from typing import Iterable

from .ledger import Ledger


def main(argv: Iterable[str] | None = None) -> None:
    """Command-line utilities for budget management."""
    parser = argparse.ArgumentParser(description="Budget utilities")
    sub = parser.add_subparsers(dest="cmd", required=True)

    set_p = sub.add_parser("set", help="Set monthly budget")
    set_p.add_argument("db_path", help="Path to ledger.db")
    set_p.add_argument("customer_id", help="Customer ID")
    set_p.add_argument("monthly_limit", type=float, help="Monthly budget limit")

    args = parser.parse_args(list(argv) if argv is not None else None)

    if args.cmd == "set":
        ledger = Ledger(args.db_path)
        ledger.set_budget(args.customer_id, float(args.monthly_limit))


def cli() -> None:
    main()


if __name__ == "__main__":
    cli()
