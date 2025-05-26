import base64
import json
import os
import time
import urllib.request
import urllib.parse
from typing import Optional, List, Dict

from .accounting import netsuite

from .fx import convert
from .fx_rates import get_rates
from .accounting.quickbooks import send_invoice_to_quickbooks

from .ledger import Ledger

USAGE_API_URL = "https://api.stripe.com/v1/usage_records"


class StripeUsageClient:
    """Creates usage records via Stripe Billing API."""

    def __init__(self, api_key: str):
        self.api_key = api_key

    def create_usage_record(
        self, subscription_item: str, quantity: int, timestamp: int
    ) -> Dict:
        data = urllib.parse.urlencode(
            {
                "subscription_item": subscription_item,
                "quantity": quantity,
                "timestamp": timestamp,
                "action": "increment",
            }
        ).encode()
        req = urllib.request.Request(USAGE_API_URL, data=data)
        auth_header = base64.b64encode(f"{self.api_key}:".encode()).decode()
        req.add_header("Authorization", f"Basic {auth_header}")
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read())


class BillingService:
    """Maps ledger events to Stripe usage records and consolidates invoices."""

    def __init__(self, api_key: str, ledger: Optional[Ledger] = None):
        self.ledger = ledger or Ledger()
        self.client = StripeUsageClient(api_key)

    def sync_usage_events(self) -> int:
        events = self.ledger.get_pending_usage_events()
        for ev in events:
            resp = self.client.create_usage_record(
                subscription_item=ev["feature"],
                quantity=ev["units"],
                timestamp=(
                    int(time.mktime(time.strptime(ev["ts"], "%Y-%m-%d %H:%M:%S")))
                    if isinstance(ev["ts"], str)
                    else int(ev["ts"])
                ),
            )
            self.ledger.mark_usage_synced(ev["id"], resp.get("id", ""))
        return len(events)

    def consolidate_invoices(self, cycle: str, currency: str = "USD") -> List[Dict]:
        events = self.ledger.get_usage_events_by_cycle(cycle)
        totals: Dict[str, float] = {}
        credits: Dict[str, float] = {}
        for ev in events:
            amount = ev["units"] * ev["unit_cost"]
            if ev["units"] >= 0:
                totals.setdefault(ev["customer_id"], 0.0)
                totals[ev["customer_id"]] += amount
            else:
                credits.setdefault(ev["customer_id"], 0.0)
                credits[ev["customer_id"]] += -amount
        invoices = []
        rates = get_rates()
        for cust, total in totals.items():
            amt = total
            if currency != "USD" and rates:
                amt = convert(total, "USD", currency, rates)
            invoice_id = f"{cust}-{cycle}"
            self.ledger.create_invoice(invoice_id, cust, cycle, amt)
            credit_amount = credits.get(cust, 0.0)
            if credit_amount:
                note_id = f"{invoice_id}-credit"
                self.ledger.create_credit_note(
                    note_id, invoice_id, credit_amount, "Usage credit"
                )

            qb_token = os.getenv("QUICKBOOKS_TOKEN")
            if qb_token:
                send_invoice_to_quickbooks(
                    {
                        "invoice_id": invoice_id,
                        "customer_id": cust,
                        "amount": amt,
                        "cycle": cycle,
                        "credit": credit_amount,
                        "currency": currency,
                    },
                    qb_token,
                )

            invoice_data = {
                "invoice_id": invoice_id,
                "customer_id": cust,
                "cycle": cycle,
                "total": amt,
                "credit": credit_amount,
            }
            try:
                netsuite.push_invoice(invoice_data)
            except Exception:
                pass

              invoices.append(
                {"invoice_id": invoice_id, "total": amt, "credit": credit_amount}
            )
        return invoices
