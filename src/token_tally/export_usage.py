import argparse
import csv
from typing import Iterable

from .ledger import Ledger


def export_usage(
    start: str, end: str, out_csv: str, ledger: Ledger | None = None
) -> None:
    """Write usage events between ``start`` and ``end`` to ``out_csv``."""
    ledger = ledger or Ledger()
    events = ledger.get_usage_events_by_range(start, end)
    with open(out_csv, "w", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(
            ["customer_id", "feature", "provider", "model", "tokens", "cost"]
        )
        for ev in events:
            tokens = ev.get("units", 0)
            cost = tokens * ev.get("unit_cost", 0.0)
            writer.writerow(
                [
                    ev.get("customer_id", ""),
                    ev.get("feature", ""),
                    ev.get("provider", ""),
                    ev.get("model", ""),
                    tokens,
                    cost,
                ]
            )


def main(argv: Iterable[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Export usage records to CSV")
    parser.add_argument("--start", required=True, help="YYYY-MM-DD")
    parser.add_argument("--end", required=True, help="YYYY-MM-DD")
    parser.add_argument("out_csv", help="Output CSV file")
    args = parser.parse_args(list(argv) if argv is not None else None)
    export_usage(args.start, args.end, args.out_csv)


if __name__ == "__main__":
    main()
