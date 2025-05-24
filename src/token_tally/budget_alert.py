from __future__ import annotations

import argparse
from datetime import datetime, UTC
from typing import Optional, Dict

from .ledger import Ledger
from .alerts import send_webhook_message


def run(db_path: str, webhook_url: str, cycle: Optional[str] = None) -> None:
    """Check spend against monthly budgets and send alerts."""
    ledger = Ledger(db_path)
    cycle = cycle or datetime.now(UTC).strftime("%Y-%m")

    events = ledger.get_usage_events_by_cycle(cycle)
    spend: Dict[str, float] = {}
    for ev in events:
        spend.setdefault(ev["customer_id"], 0.0)
        spend[ev["customer_id"]] += ev["units"] * ev["unit_cost"]

    for cust_id, limit in ledger.list_budgets():
        total = spend.get(cust_id, 0.0)
        if total > limit:
            message = f"Customer {cust_id} exceeded budget: {total:.2f} / {limit:.2f}"
            send_webhook_message(webhook_url, message)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Send budget alerts")
    parser.add_argument("db_path", help="Path to ledger.db")
    parser.add_argument("webhook_url", help="Webhook URL")
    parser.add_argument("--cycle", help="Invoice cycle YYYY-MM")
    args = parser.parse_args()
    run(args.db_path, args.webhook_url, args.cycle)
