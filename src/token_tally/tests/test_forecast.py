import sys
import pathlib

sys.path.append(str(pathlib.Path(__file__).resolve().parents[2]))
from datetime import datetime, timedelta, UTC

from token_tally import UsageLedger, UsageEvent, arima_forecast, forecast_next_hour


def test_arima_constant():
    assert arima_forecast([1, 2, 3, 4]) == 5


def test_hourly_totals_and_forecast(tmp_path):
    db = tmp_path / "ledger.db"
    ledger = UsageLedger(db_path=str(db))
    now = datetime.now(UTC).replace(minute=0, second=0, microsecond=0)
    for i in range(3):
        event = UsageEvent(
            event_id=f"e{i}",
            ts=now - timedelta(hours=3 - i),
            customer_id="cust",
            provider="openai",
            model="gpt",
            metric_type="tokens",
            units=10,
            unit_cost_usd=0.5,
        )
        ledger.add_event(event)
    totals = ledger.get_hourly_totals(4)
    forecast = forecast_next_hour(ledger, hours=4)
    assert forecast > 0
