import sys
import pathlib

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1] / "src"))
from datetime import datetime, UTC
from token_tally import UsageEvent, UsageLedger


def test_add_event(tmp_path):
    db_path = tmp_path / "ledger.db"
    ledger = UsageLedger(db_path=str(db_path))
    event = UsageEvent(
        event_id="evt1",
        ts=datetime.now(UTC),
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


def test_dead_letter_on_malformed(tmp_path):
    db_path = tmp_path / "ledger.db"
    ledger = UsageLedger(db_path=str(db_path))
    bad = {"event_id": "bad1", "ts": "not-a-date"}
    event = ledger.parse_event(bad)
    assert event is None

    import sqlite3, json

    with sqlite3.connect(db_path) as conn:
        cur = conn.execute("SELECT raw, error FROM dead_letter_events")
        row = cur.fetchone()
    assert row is not None
    raw = json.loads(row[0])
    assert raw["event_id"] == "bad1"
    assert "invalid" in row[1].lower()


def test_dead_letter_timestamp_timezone(tmp_path):
    db_path = tmp_path / "ledger.db"
    ledger = UsageLedger(db_path=str(db_path))
    ledger.parse_event({"event_id": "bad2", "ts": "bad"})

    import sqlite3

    with sqlite3.connect(db_path) as conn:
        cur = conn.execute("SELECT ts FROM dead_letter_events")
        ts = cur.fetchone()[0]

    assert "+00:00" in ts
