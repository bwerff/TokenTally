import sys
import pathlib
from datetime import datetime, timedelta, UTC

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from token_tally import UsageEvent, ClickHouseUsageLedger
import token_tally.usage_ledger as usage_ledger


class DummyClient:
    def __init__(self):
        self.rows = []

    def execute(self, query, params=None):
        stmt = query.strip().split()[0].upper()
        if stmt == "INSERT":
            self.rows.extend(params)
        elif stmt == "SELECT":
            start = params["start"]
            end = params["end"]
            return [
                (row[1], row[6], row[7]) for row in self.rows if start <= row[1] < end
            ]
        else:
            return None


def test_clickhouse_ledger_add_and_totals(monkeypatch):
    dummy = DummyClient()
    monkeypatch.setattr(usage_ledger, "Client", lambda *a, **k: dummy)
    ledger = ClickHouseUsageLedger(host="dummy")
    now = datetime.now(UTC).replace(minute=0, second=0, microsecond=0)
    event = UsageEvent(
        event_id="e1",
        ts=now - timedelta(hours=1),
        customer_id="cust",
        provider="openai",
        model="gpt-4",
        metric_type="tokens",
        units=2,
        unit_cost_usd=0.5,
    )
    ledger.add_event(event)

    assert dummy.rows

    totals = ledger.get_hourly_totals(2)
    assert totals[1] == 1.0
