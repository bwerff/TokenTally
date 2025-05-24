import sys
import pathlib

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from datetime import datetime
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
