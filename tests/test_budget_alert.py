import sys
import pathlib

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from token_tally.ledger import Ledger
import token_tally.budget_alert as budget_alert


def test_budget_alert(tmp_path, monkeypatch):
    db = tmp_path / "ledger.db"
    ledger = Ledger(str(db))
    ledger.set_budget("cust1", 50.0)
    ledger.set_budget("cust2", 30.0)
    ledger.add_usage_event("e1", "cust1", "feat", 10, 6.0, "2024-05")
    ledger.add_usage_event("e2", "cust2", "feat", 3, 5.0, "2024-05")

    calls = []

    def fake_send(url, msg):
        calls.append((url, msg))

    monkeypatch.setattr(budget_alert, "send_webhook_message", fake_send)
    budget_alert.run(str(db), "http://hook", cycle="2024-05")

    assert len(calls) == 1
    assert calls[0][0] == "http://hook"
    assert "cust1" in calls[0][1]
