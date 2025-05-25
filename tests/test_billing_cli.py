import os
import sys
import pathlib
import subprocess

BASE_DIR = pathlib.Path(__file__).resolve().parents[1]
SRC_DIR = BASE_DIR / "src"

from token_tally.ledger import Ledger  # noqa: E402


def test_billing_cli_sync(tmp_path):
    db_path = tmp_path / "ledger.db"
    ledger = Ledger(str(db_path))
    ledger.add_usage_event("e1", "cust", "feat", 5, 0.1, "2024-05")

    # create sitecustomize to stub network call
    sitecustomize = tmp_path / "sitecustomize.py"
    sitecustomize.write_text(
        """
from token_tally.billing import StripeUsageClient

def _fake(self, subscription_item, quantity, timestamp):
    return {"id": "dummy"}

StripeUsageClient.create_usage_record = _fake
"""
    )

    env = os.environ.copy()
    env["PYTHONPATH"] = os.pathsep.join([str(tmp_path), str(SRC_DIR)])

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "token_tally.billing_cli",
            "sync",
            str(db_path),
            "sk_test",
        ],
        capture_output=True,
        text=True,
        cwd=tmp_path,
        env=env,
        check=True,
    )
    assert result.stdout.strip() == "1"
    ledger = Ledger(str(db_path))
    assert ledger.get_pending_usage_events() == []
