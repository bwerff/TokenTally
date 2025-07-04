import sys, pathlib

sys.path.append(str(pathlib.Path(__file__).resolve().parents[2]))

from token_tally.billing import BillingService, StripeUsageClient
import token_tally.accounting.netsuite as netsuite
from token_tally.ledger import Ledger


class DummyClient(StripeUsageClient):
    def __init__(self):
        pass

    def create_usage_record(self, subscription_item, quantity, timestamp):
        return {"id": f"usage-{subscription_item}-{quantity}"}


def test_sync_usage_events(tmp_path):
    db = tmp_path / "ledger.db"
    ledger = Ledger(str(db))
    ledger.add_usage_event(
        "e1", "cust", "item1", 5, 1.0, "2024-05", business_unit="sales"
    )
    service = BillingService("sk_test", ledger)
    service.client = DummyClient()
    count = service.sync_usage_events()
    assert count == 1
    events = ledger.get_pending_usage_events()
    assert events == []


def test_consolidate_invoices(tmp_path, monkeypatch):
    db = tmp_path / "ledger.db"
    ledger = Ledger(str(db))
    ledger.add_usage_event(
        "e1", "cust", "item1", 10, 2.0, "2024-05", business_unit="sales"
    )
    ledger.add_usage_event(
        "e2", "cust", "item1", -2, 2.0, "2024-05", business_unit="sales"
    )
    service = BillingService("sk_test", ledger)
    service.client = DummyClient()
    monkeypatch.setattr(netsuite, "push_invoice", lambda invoice: {"status": "ok"})
    invoices = service.consolidate_invoices("2024-05")
    assert invoices == [{"invoice_id": "cust-2024-05", "total": 20.0, "credit": 4.0}]


def test_consolidate_invoices_fx(tmp_path, monkeypatch):
    db = tmp_path / "ledger.db"
    ledger = Ledger(str(db))
    ledger.add_usage_event(
        "e1", "cust", "item1", 10, 2.0, "2024-05", business_unit="sales"
    )
    service = BillingService("sk_test", ledger)
    service.client = DummyClient()
    monkeypatch.setattr(netsuite, "push_invoice", lambda invoice: {"status": "ok"})

    monkeypatch.setattr(
        "token_tally.billing.get_rates",
        lambda: {"USD": 1.0, "EUR": 0.9},
    )
    invoices = service.consolidate_invoices("2024-05", currency="EUR")
    assert invoices == [{"invoice_id": "cust-2024-05", "total": 18.0, "credit": 0.0}]
