import sys
import pathlib

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from token_tally.fx import parse_ecb_rates, convert, get_intraday_rates, INTRADAY_URL
from token_tally import fx_rates
from token_tally.fx_rates import store_rates, get_rates, fetch_and_store


def test_parse_ecb_rates():
    xml = (
        b"<?xml version='1.0' encoding='UTF-8'?>"
        b"<gesmes:Envelope xmlns:gesmes='http://www.gesmes.org/xml/2002-08-01' "
        b"xmlns='http://www.ecb.int/vocabulary/2002-08-01/eurofxref'>"
        b"<Cube><Cube time='2024-05-31'>"
        b"<Cube currency='USD' rate='1.1'/><Cube currency='GBP' rate='0.9'/>"
        b"</Cube></Cube></gesmes:Envelope>"
    )
    rates = parse_ecb_rates(xml)
    assert rates["USD"] == 1.1
    amount = convert(1.0, "USD", "GBP", rates)
    expected = 1.0 / 1.1 * 0.9
    assert round(amount, 6) == round(expected, 6)


def test_store_and_get_rates(tmp_path):
    db = tmp_path / "fx.db"
    store_rates({"USD": 1.1, "EUR": 1.0}, db_path=str(db), fetch_date="2024-05-31")
    rates = get_rates(db_path=str(db))
    assert rates["USD"] == 1.1


def test_get_intraday_rates(monkeypatch):
    xml = (
        b"<?xml version='1.0' encoding='UTF-8'?>"
        b"<gesmes:Envelope xmlns:gesmes='http://www.gesmes.org/xml/2002-08-01' "
        b"xmlns='http://www.ecb.int/vocabulary/2002-08-01/eurofxref'>"
        b"<Cube><Cube time='2024-05-31'>"
        b"<Cube currency='USD' rate='1.1'/><Cube currency='GBP' rate='0.9'/>"
        b"</Cube></Cube></gesmes:Envelope>"
    )

    class DummyResp:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            pass

        def read(self):
            return xml

    called = {}

    def fake_open(url):
        called["url"] = url
        return DummyResp()

    monkeypatch.setattr("urllib.request.urlopen", fake_open)
    rates = get_intraday_rates()
    assert called["url"] == INTRADAY_URL
    assert rates["USD"] == 1.1


def test_fetch_and_store_intraday(tmp_path, monkeypatch):
    db = tmp_path / "fx.db"

    def fake_rates():
        return {"EUR": 1.0, "USD": 1.2}

    monkeypatch.setattr(fx_rates, "get_intraday_rates", fake_rates)
    fetch_and_store(db_path=str(db), intraday=True)
    rates = get_rates(db_path=str(db))
    assert rates["USD"] == 1.2
