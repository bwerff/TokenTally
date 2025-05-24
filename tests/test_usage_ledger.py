import sys
import pathlib
sys.path.append(str(pathlib.Path(__file__).resolve().parents[1] / "src"))
from datetime import datetime
from token_tally import UsageEvent, UsageLedger


def test_add_event(tmp_path):
    db_path = tmp_path / "ledger.db"
    ledger = UsageLedger(db_path=str(db_path))
    event = UsageEvent(
        event_id="evt1",
        ts=datetime.utcnow(),
        customer_id="cust",
        provider="openai",
        model="gpt-4",
        metric_type="tokens",
        units=5,
        unit_cost_usd=0.01,
    )
    ledger.add_event(event)
    # Verify row saved
    import sqlite3

    with sqlite3.connect(db_path) as conn:
        cur = conn.execute("SELECT count(*) FROM usage_events")
        count = cur.fetchone()[0]
    assert count == 1
