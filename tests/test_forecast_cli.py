import os
import sys
import pathlib
import subprocess
from datetime import datetime, timedelta, UTC

BASE_DIR = pathlib.Path(__file__).resolve().parents[1]
SRC_DIR = BASE_DIR / "src"

sys.path.append(str(SRC_DIR))

from token_tally import UsageEvent, UsageLedger  # noqa: E402


def test_forecast_cli(tmp_path):
    db_path = tmp_path / "ledger.db"
    ledger = UsageLedger(str(db_path))
    now = datetime.now(UTC).replace(minute=0, second=0, microsecond=0)
    event = UsageEvent(
        event_id="e1",
        ts=now - timedelta(hours=1),
        customer_id="cust",
        provider="openai",
        model="gpt",
        metric_type="tokens",
        units=10,
        unit_cost_usd=0.5,
    )
    ledger.add_event(event)

    env = os.environ.copy()
    env["PYTHONPATH"] = str(SRC_DIR)
    result = subprocess.run(
        [sys.executable, "-m", "token_tally.forecast_cli", str(db_path)],
        capture_output=True,
        text=True,
        cwd=tmp_path,
        env=env,
        check=True,
    )
    assert float(result.stdout.strip()) > 0.0
