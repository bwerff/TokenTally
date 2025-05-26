import sqlite3
from datetime import date
from typing import Dict, Optional

from .fx import get_ecb_rates, get_intraday_rates

DB_PATH = "fx_rates.db"


def _ensure_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS fx_rates (
            date TEXT NOT NULL,
            currency TEXT NOT NULL,
            rate REAL NOT NULL,
            PRIMARY KEY (date, currency)
        )
        """
    )


def store_rates(
    rates: Dict[str, float], fetch_date: Optional[str] = None, db_path: str = DB_PATH
) -> str:
    """Persist a mapping of currency rates for a given date."""
    fetch_date = fetch_date or date.today().isoformat()
    with sqlite3.connect(db_path) as conn:
        _ensure_table(conn)
        for cur, rate in rates.items():
            conn.execute(
                "INSERT OR REPLACE INTO fx_rates (date, currency, rate) VALUES (?, ?, ?)",
                (fetch_date, cur, rate),
            )
        conn.commit()
    return fetch_date


def fetch_and_store(db_path: str = DB_PATH, *, intraday: bool = False) -> str:
    """Fetch latest FX rates and store them.

    If ``intraday`` is True, use the intraday feed instead of the daily ECB feed.
    """
    rates = get_intraday_rates() if intraday else get_ecb_rates()
    return store_rates(rates, db_path=db_path)


def get_rates(
    fetch_date: Optional[str] = None, db_path: str = DB_PATH
) -> Dict[str, float]:
    """Load rates for the specified date or the most recent available."""
    with sqlite3.connect(db_path) as conn:
        _ensure_table(conn)
        if fetch_date is None:
            cur = conn.execute("SELECT MAX(date) FROM fx_rates")
            row = cur.fetchone()
            fetch_date = row[0] if row and row[0] else None
            if fetch_date is None:
                return {}
        cur = conn.execute(
            "SELECT currency, rate FROM fx_rates WHERE date = ?", (fetch_date,)
        )
        return {cur: rate for cur, rate in cur.fetchall()}


def main(argv: Optional[list[str]] = None) -> None:
    argv = argv or []
    if argv and argv[0] == "fetch":
        intraday = "--intraday" in argv[1:]
        fetch_date = fetch_and_store(intraday=intraday)
        print(f"Stored FX rates for {fetch_date}")
    else:
        print("Usage: python -m token_tally.fx_rates fetch [--intraday]")


if __name__ == "__main__":
    import sys

    main(sys.argv[1:])
