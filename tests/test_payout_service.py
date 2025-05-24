import sys
import pathlib

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from token_tally import PayoutService, Ledger


def test_record_and_retrieve(tmp_path):
    db = tmp_path / "ledger.db"
    service = PayoutService(Ledger(str(db)))
    service.record_payout("p1", "u1", 500, "USD")
    assert service.get_status("p1") == "pending"
    service.update_status("p1", "paid")
    assert service.get_status("p1") == "paid"
