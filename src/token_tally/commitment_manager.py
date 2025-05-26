from __future__ import annotations

import argparse
from datetime import datetime, timedelta, UTC
from typing import Dict, Iterable

from .ledger import Ledger


def suggest_commitments(
    ledger: Ledger,
    months: int = 3,
    reserve_ratio: float = 0.8,
) -> Dict[str, float]:
    """Return commitment suggestions keyed by customer_id."""
    start_dt = datetime.now(UTC) - timedelta(days=30 * months)
    start = start_dt.strftime("%Y-%m-%d")
    end = datetime.now(UTC).strftime("%Y-%m-%d")
    events = ledger.get_usage_events_by_range(start, end)
    totals: Dict[str, float] = {}
    for ev in events:
        cost = ev.get("units", 0) * ev.get("unit_cost", 0.0)
        cust = ev.get("customer_id", "")
        totals[cust] = totals.get(cust, 0.0) + cost
    avg_per_month = {cid: total / months for cid, total in totals.items()}
    return {cid: round(avg * reserve_ratio, 2) for cid, avg in avg_per_month.items()}


def main(argv: Iterable[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Reserved capacity commitment manager")
    sub = parser.add_subparsers(dest="cmd", required=True)
    analyze_p = sub.add_parser("analyze", help="Analyze historical usage")
    analyze_p.add_argument("db_path", help="Path to ledger.db")
    analyze_p.add_argument(
        "--months",
        type=int,
        default=3,
        help="Number of months to analyze",
    )
    args = parser.parse_args(list(argv) if argv is not None else None)

    if args.cmd == "analyze":
        ledger = Ledger(args.db_path)
        suggestions = suggest_commitments(ledger, months=args.months)
        for cust_id in sorted(suggestions):
            print(f"{cust_id},{suggestions[cust_id]:.2f}")


def cli() -> None:
    main()


if __name__ == "__main__":
    cli()
