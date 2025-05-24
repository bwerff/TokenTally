import sys
import pathlib

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from datetime import datetime
from hashlib import sha256
import sqlite3
from token_tally.audit import AuditLog


def test_add_and_list(tmp_path):
    db_path = tmp_path / "audit.db"
    log = AuditLog(str(db_path))
    log.add_event("evt1", "cust", "hello world", 5, datetime(2024, 1, 1))
    events = log.list_events()
    assert len(events) == 1
    assert events[0]["event_id"] == "evt1"
    assert events[0]["customer_id"] == "cust"
    assert events[0]["token_count"] == 5
    expected_hash = sha256(("" + events[0]["prompt_hash"]).encode("utf-8")).hexdigest()
    assert events[0]["prev_hash"] == expected_hash


def test_hash_chain_verification(tmp_path):
    db_path = tmp_path / "audit.db"
    log = AuditLog(str(db_path))
    log.add_event("evt1", "cust", "hello", 1, datetime(2024, 1, 1))
    log.add_event("evt2", "cust", "world", 2, datetime(2024, 1, 2))
    assert log.verify_chain("cust")

    with sqlite3.connect(db_path) as conn:
        conn.execute(
            "UPDATE audit_events SET prev_hash = 'bad' WHERE event_id = 'evt2'"
        )
        conn.commit()

    assert not log.verify_chain("cust")
