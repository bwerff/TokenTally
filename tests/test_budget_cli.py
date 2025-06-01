import os
import sys
import pathlib
import subprocess

BASE_DIR = pathlib.Path(__file__).resolve().parents[1]
SRC_DIR = BASE_DIR / "src"

sys.path.append(str(SRC_DIR))

from token_tally.ledger import Ledger  # noqa: E402


def test_budget_cli_set(tmp_path):
    db_path = tmp_path / "ledger.db"

    env = os.environ.copy()
    env["PYTHONPATH"] = str(SRC_DIR)

    subprocess.run(
        [
            sys.executable,
            "-m",
            "token_tally.budget_cli",
            "set",
            str(db_path),
            "cust1",
            "123.45",
        ],
        capture_output=True,
        text=True,
        cwd=tmp_path,
        env=env,
        check=True,
    )

    ledger = Ledger(str(db_path))
    assert ledger.get_budget("cust1") == 123.45
