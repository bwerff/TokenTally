import sys, pathlib
sys.path.append(str(pathlib.Path(__file__).resolve().parents[2]))

from token_tally.billing import BillingService, StripeUsageClient
from token_tally.ledger import Ledger

class DummyClient(StripeUsageClient):
    def __init__(self):
        pass
    def create_usage_record(self, subscription_item, quantity, timestamp):
        return {"id": f"usage-{subscription_item}-{quantity}"}

def test_sync_usage_events(tmp_path):
    db = tmp_path / "ledger.db"
    ledger = Ledger(str(db))
    ledger.add_usage_event("e1", "cust", "item1", 5, 1.0, "2024-05")
    service = BillingService("sk_test", ledger)
    service.client = DummyClient()
    count = service.sync_usage_events()
    assert count == 1
    events = ledger.get_pending_usage_events()
    assert events == []

def test_consolidate_invoices(tmp_path):
    db = tmp_path / "ledger.db"
    ledger = Ledger(str(db))
    ledger.add_usage_event("e1", "cust", "item1", 10, 2.0, "2024-05")
    ledger.add_usage_event("e2", "cust", "item1", -2, 2.0, "2024-05")
    service = BillingService("sk_test", ledger)
    service.client = DummyClient()
    invoices = service.consolidate_invoices("2024-05")
    assert invoices == [{"invoice_id": "cust-2024-05", "total": 20.0, "credit": 4.0}]

