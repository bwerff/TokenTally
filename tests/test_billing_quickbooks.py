import sys
import pathlib

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from token_tally.billing import BillingService
from token_tally.ledger import Ledger


def test_consolidate_invoices_quickbooks(tmp_path, monkeypatch):
    db = tmp_path / "ledger.db"
    ledger = Ledger(str(db))
    ledger.add_usage_event("e1", "cust", "feat", 5, 1.0, "2024-05")
    service = BillingService("sk", ledger)

    sent = {}

    def fake_send(invoice, token):
        sent["invoice"] = invoice
        sent["token"] = token
        return {"id": "qb1"}

    monkeypatch.setattr("token_tally.billing.send_invoice_to_quickbooks", fake_send)
    monkeypatch.setenv("QUICKBOOKS_TOKEN", "tok")
    service.consolidate_invoices("2024-05")
    assert sent["token"] == "tok"
    assert sent["invoice"]["invoice_id"] == "cust-2024-05"


def test_consolidate_invoices_no_quickbooks(tmp_path, monkeypatch):
    db = tmp_path / "ledger.db"
    ledger = Ledger(str(db))
    ledger.add_usage_event("e1", "cust", "feat", 5, 1.0, "2024-05")
    service = BillingService("sk", ledger)

    called = {"count": 0}

    def fake_send(invoice, token):
        called["count"] += 1
        return {}

    monkeypatch.setattr("token_tally.billing.send_invoice_to_quickbooks", fake_send)
    monkeypatch.delenv("QUICKBOOKS_TOKEN", raising=False)
    service.consolidate_invoices("2024-05")
    assert called["count"] == 0
