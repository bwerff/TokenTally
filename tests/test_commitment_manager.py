import os
import sys
import pathlib
import subprocess
from datetime import datetime, timedelta, UTC

BASE_DIR = pathlib.Path(__file__).resolve().parents[1]
SRC_DIR = BASE_DIR / "src"

sys.path.append(str(SRC_DIR))

from token_tally.ledger import Ledger  # noqa: E402


def test_commitment_analyze_cli(tmp_path):
    db_path = tmp_path / "ledger.db"
    ledger = Ledger(str(db_path))
    now = datetime.now(UTC)
    ledger.add_usage_event(
        "e1",
        "cust1",
        "feat",
        10,
        1.0,
        "2024-05",
        ts=now - timedelta(days=10),
    )
    ledger.add_usage_event(
        "e2",
        "cust1",
        "feat",
        10,
        1.0,
        "2024-04",
        ts=now - timedelta(days=40),
    )
    ledger.add_usage_event(
        "e3",
        "cust2",
        "feat",
        20,
        2.0,
        "2024-05",
        ts=now - timedelta(days=5),
    )

    env = os.environ.copy()
    env["PYTHONPATH"] = str(SRC_DIR)
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "token_tally.commitment_manager",
            "analyze",
            str(db_path),
        ],
        capture_output=True,
        text=True,
        cwd=tmp_path,
        env=env,
        check=True,
    )
    lines = result.stdout.strip().splitlines()
    data = dict(line.split(",") for line in lines if line)
    assert abs(float(data["cust1"]) - 5.33) < 0.01
    assert abs(float(data["cust2"]) - 10.67) < 0.01
