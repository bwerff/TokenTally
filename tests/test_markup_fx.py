import pathlib
import sys

BASE_DIR = pathlib.Path(__file__).resolve().parents[1]
sys.path.append(str(BASE_DIR / "src"))

from datetime import datetime
import sqlite3

from token_tally.markup import MarkupRuleStore, get_effective_markup  # noqa: E402
from token_tally.fx import parse_ecb_rates, convert  # noqa: E402
from token_tally.ledger import Ledger  # noqa: E402


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


def test_event_markup_and_fx(tmp_path):
    rule_db = tmp_path / "rules.db"
    ledger_db = tmp_path / "ledger.db"

    store = MarkupRuleStore(str(rule_db))
    store.create_rule("r1", "openai", "gpt-4", 0.1, "2024-01-01")

    rates = {"EUR": 1.0, "USD": 1.1}

    ledger = Ledger(str(ledger_db))
    ledger.add_usage_event(
        "e1",
        "cust",
        "feat",
        1,
        0.02,
        "2024-06",
        provider="openai",
        model="gpt-4",
        currency="EUR",
        fx_rates=rates,
        ts=datetime(2024, 6, 1),
        markup_db_path=str(rule_db),
    )

    with sqlite3.connect(ledger_db) as conn:
        cur = conn.execute("SELECT unit_cost FROM usage_events WHERE id = 'e1'")
        stored = cur.fetchone()[0]

    expected = convert(0.02 * 1.1, "EUR", "USD", rates)
    assert round(stored, 6) == round(expected, 6)
