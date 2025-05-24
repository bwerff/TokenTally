import pathlib
import sys

BASE_DIR = pathlib.Path(__file__).resolve().parents[1]
sys.path.append(str(BASE_DIR / "src"))

from token_tally.markup import MarkupRuleStore  # noqa: E402
from token_tally.fx import parse_ecb_rates, convert  # noqa: E402


def test_markup_rule_crud(tmp_path):
    db = tmp_path / "rules.db"
    store = MarkupRuleStore(str(db))
    store.create_rule("1", "openai", "gpt-4o", 0.2, "2025-01-01")
    rule = store.get_rule("1")
    assert rule["provider"] == "openai"
    store.update_rule("1", markup=0.3)
    assert store.get_rule("1")["markup"] == 0.3
    assert len(store.list_rules()) == 1
    store.delete_rule("1")
    assert store.get_rule("1") is None


def test_parse_rates_and_convert():
    xml = b"""<?xml version='1.0' encoding='UTF-8'?>\n"""
    xml += (
        b"<gesmes:Envelope xmlns:gesmes='http://www.gesmes.org/xml/2002-08-01' "
        b"xmlns='http://www.ecb.int/vocabulary/2002-08-01/eurofxref'>"
        b"<Cube><Cube time='2024-05-31'>"
        b"<Cube currency='USD' rate='1.1'/><Cube currency='GBP' rate='0.9'/>"
        b"</Cube></Cube></gesmes:Envelope>"
    )
    rates = parse_ecb_rates(xml)
    assert rates["USD"] == 1.1
    amount_gbp = convert(1.0, "USD", "GBP", rates)
    expected = 1.0 / 1.1 * 0.9
    assert round(amount_gbp, 6) == round(expected, 6)
