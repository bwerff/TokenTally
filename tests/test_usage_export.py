import os
import sys
import pathlib
import subprocess

BASE_DIR = pathlib.Path(__file__).resolve().parents[1]
sys.path.append(str(BASE_DIR / "src"))

from token_tally.ledger import Ledger  # noqa: E402


def _dummy_snowflake(monkeypatch, rows):
    class _Cursor:
        def executemany(self, query, params):
            rows.extend(params)

    class _Conn:
        def cursor(self):
            return _Cursor()

        def close(self):
            pass

    import types, sys

    sf_mod = types.ModuleType("connector")
    sf_mod.connect = lambda **k: _Conn()
    pkg = types.ModuleType("snowflake")
    pkg.connector = sf_mod
    sys.modules.setdefault("snowflake", pkg)
    sys.modules.setdefault("snowflake.connector", sf_mod)


def test_export_usage_cli(tmp_path):
    db_path = tmp_path / "ledger.db"
    ledger = Ledger(str(db_path))
    ledger.add_usage_event("e1", "cust1", "feat", 10, 0.1, "2024-05")
    ledger.add_usage_event("e2", "cust2", "feat", 5, 0.2, "2024-05")
    out_csv = tmp_path / "out.csv"
    env = os.environ.copy()
    env["PYTHONPATH"] = str(BASE_DIR / "src")
    subprocess.run(
        [
            sys.executable,
            "-m",
            "token_tally.export_usage",
            "--start",
            "2020-01-01",
            "--end",
            "2030-01-01",
            str(out_csv),
        ],
        cwd=tmp_path,
        env=env,
        check=True,
    )
    lines = out_csv.read_text().strip().splitlines()
    assert lines[0] == "customer_id,feature,provider,model,tokens,cost"
    assert "cust1" in lines[1]
    assert "cust2" in lines[2]


def test_snowflake_export_cli(tmp_path, monkeypatch):
    db_path = tmp_path / "ledger.db"
    ledger = Ledger(str(db_path))
    ledger.add_usage_event("e1", "cust1", "feat", 10, 0.1, "2024-05")
    ledger.add_usage_event("e2", "cust2", "feat", 5, 0.2, "2024-05")
    rows = []
    _dummy_snowflake(monkeypatch, rows)
    env_vars = {
        "SNOWFLAKE_ACCOUNT": "acc",
        "SNOWFLAKE_USER": "user",
        "SNOWFLAKE_PASSWORD": "pass",
        "SNOWFLAKE_DATABASE": "db",
        "SNOWFLAKE_SCHEMA": "public",
        "SNOWFLAKE_WAREHOUSE": "wh",
    }
    for k, v in env_vars.items():
        monkeypatch.setenv(k, v)
    from token_tally.export import snowflake_export

    monkeypatch.setattr(snowflake_export, "Ledger", lambda: ledger)
    snowflake_export.main(["--start", "2020-01-01", "--end", "2030-01-01"])
    assert len(rows) == 2
    assert rows[0][0] == "cust1"
    assert rows[1][0] == "cust2"
