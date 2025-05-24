import sys, pathlib
sys.path.append(str(pathlib.Path(__file__).resolve().parents[2]))
from pathlib import Path
from receipt_processor.offer_matching import OfferMatcher


def test_match_line_by_upc(tmp_path):
    offers_path = tmp_path / "offers.json"
    offers_path.write_text('[{"upc": "111222333444", "name": "Test Prod"}]')
    matcher = OfferMatcher(offers_path)
    assert matcher.match_line("111222333444 SOME ITEM") == {"upc": "111222333444", "name": "Test Prod"}


def test_match_line_by_name(tmp_path):
    offers_path = tmp_path / "offers.json"
    offers_path.write_text('[{"upc": "555", "name": "Special Snack"}]')
    matcher = OfferMatcher(offers_path)
    assert matcher.match_line("special snack large") == {"upc": "555", "name": "Special Snack"}
