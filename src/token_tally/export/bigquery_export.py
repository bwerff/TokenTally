import argparse
from typing import Iterable

from ..ledger import Ledger

try:
    from google.cloud import bigquery
except ImportError:  # pragma: no cover - optional dependency
    bigquery = None  # type: ignore


def export_usage(
    start: str,
    end: str,
    project: str,
    dataset: str,
    table: str,
    *,
    ledger: Ledger | None = None,
) -> None:
    """Write usage events between ``start`` and ``end`` to BigQuery."""

    if bigquery is None:
        raise ImportError("google-cloud-bigquery not installed")

    ledger = ledger or Ledger()
    client = bigquery.Client(project=project)
    table_ref = client.dataset(dataset).table(table)
    events = ledger.get_usage_events_by_range(start, end)
    rows = []
    for ev in events:
        rows.append(
            {
                "customer_id": ev.get("customer_id", ""),
                "feature": ev.get("feature", ""),
                "units": ev.get("units", 0),
                "unit_cost": ev.get("unit_cost", 0.0),
                "ts": ev.get("ts"),
            }
        )
    errors = client.insert_rows_json(table_ref, rows)
    if errors:
        raise RuntimeError(f"failed to insert rows: {errors}")


def main(argv: Iterable[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Export usage records to BigQuery")
    parser.add_argument("--start", required=True, help="YYYY-MM-DD")
    parser.add_argument("--end", required=True, help="YYYY-MM-DD")
    parser.add_argument("--project", required=True, help="GCP project ID")
    parser.add_argument("--dataset", required=True, help="BigQuery dataset")
    parser.add_argument("--table", required=True, help="BigQuery table")
    args = parser.parse_args(list(argv) if argv is not None else None)
    export_usage(args.start, args.end, args.project, args.dataset, args.table)


if __name__ == "__main__":  # pragma: no cover - manual invocation
    main()
