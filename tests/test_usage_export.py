import os
import sys
import pathlib
import subprocess

BASE_DIR = pathlib.Path(__file__).resolve().parents[1]
sys.path.append(str(BASE_DIR / "src"))

from token_tally.ledger import Ledger  # noqa: E402
import token_tally.export.bigquery_export as bigquery_export  # noqa: E402
import types


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


def test_bigquery_export(monkeypatch, tmp_path):
    db_path = tmp_path / "ledger.db"
    ledger = Ledger(str(db_path))
    ledger.add_usage_event("e1", "cust", "feat", 3, 0.5, "2024-05")

    class DummyDataset:
        def __init__(self, client, name):
            self.client = client
            self.name = name

        def table(self, name):
            self.client.table_called = (self.name, name)
            return f"{self.name}.{name}"

    class DummyClient:
        def __init__(self):
            self.inserted = []

        def dataset(self, name):
            return DummyDataset(self, name)

        def insert_rows_json(self, table_ref, rows):
            self.table_ref = table_ref
            self.inserted.extend(rows)
            return []

    dummy = DummyClient()
    monkeypatch.setattr(
        bigquery_export,
        "bigquery",
        types.SimpleNamespace(Client=lambda project: dummy),
    )

    bigquery_export.export_usage(
        "2020-01-01",
        "2030-01-01",
        project="proj",
        dataset="ds",
        table="tbl",
        ledger=ledger,
    )

    assert dummy.table_called == ("ds", "tbl")
    assert dummy.inserted
