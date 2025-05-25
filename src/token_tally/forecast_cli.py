import argparse
from typing import Iterable

from .forecast import forecast_next_hour
from .usage_ledger import UsageLedger


def main(argv: Iterable[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Forecast next hour spend")
    parser.add_argument("db_path", help="Path to ledger.db")
    args = parser.parse_args(list(argv) if argv is not None else None)
    ledger = UsageLedger(args.db_path)
    prediction = forecast_next_hour(ledger)
    print(prediction)


def cli() -> None:
    main()


if __name__ == "__main__":
    cli()
