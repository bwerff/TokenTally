"""Export ledger usage records to Snowflake.

Required environment variables:
- ``SNOWFLAKE_ACCOUNT``
- ``SNOWFLAKE_USER``
- ``SNOWFLAKE_PASSWORD``
- ``SNOWFLAKE_DATABASE``
- ``SNOWFLAKE_SCHEMA``
- ``SNOWFLAKE_WAREHOUSE``

Optionally ``SNOWFLAKE_TABLE`` can override the destination table name.
"""

from __future__ import annotations

import argparse
import os
from typing import Iterable

try:
    import snowflake.connector as sf
except ImportError:  # pragma: no cover - snowflake-connector not installed
    sf = None  # type: ignore

from ..ledger import Ledger


def export_usage(
    start: str,
    end: str,
    *,
    ledger: Ledger | None = None,
    table: str | None = None,
) -> None:
    """Bulk insert usage events between ``start`` and ``end`` into Snowflake."""

    ledger = ledger or Ledger()
    events = ledger.get_usage_events_by_range(start, end)

    table = table or os.environ.get("SNOWFLAKE_TABLE", "USAGE_EVENTS")

    if sf is None:
        raise ImportError("snowflake-connector-python not installed")

    conn = sf.connect(
        account=os.environ["SNOWFLAKE_ACCOUNT"],
        user=os.environ["SNOWFLAKE_USER"],
        password=os.environ["SNOWFLAKE_PASSWORD"],
        database=os.environ["SNOWFLAKE_DATABASE"],
        schema=os.environ["SNOWFLAKE_SCHEMA"],
        warehouse=os.environ["SNOWFLAKE_WAREHOUSE"],
    )
    try:
        cur = conn.cursor()
        cur.executemany(
            f"INSERT INTO {table} (customer_id, feature, provider, model, tokens, cost) "
            "VALUES (%s, %s, %s, %s, %s, %s)",
            [
                (
                    ev.get("customer_id", ""),
                    ev.get("feature", ""),
                    ev.get("provider"),
                    ev.get("model"),
                    ev.get("units", 0),
                    ev.get("units", 0) * ev.get("unit_cost", 0.0),
                )
                for ev in events
            ],
        )
    finally:
        conn.close()


def main(argv: Iterable[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Export usage records to Snowflake")
    parser.add_argument("--start", required=True, help="YYYY-MM-DD")
    parser.add_argument("--end", required=True, help="YYYY-MM-DD")
    parser.add_argument("--table", help="Destination table name")
    args = parser.parse_args(list(argv) if argv is not None else None)

    export_usage(args.start, args.end, table=args.table)


def cli() -> None:
    main()


if __name__ == "__main__":
    cli()
