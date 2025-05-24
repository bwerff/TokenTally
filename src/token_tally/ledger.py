import sqlite3
from typing import Optional, Dict, Any

class Ledger:
    """Simple SQLite ledger for payout entries."""

    def __init__(self, db_path: str = "ledger.db"):
        self.db_path = db_path
        self._ensure_tables()

    def _ensure_tables(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS payouts (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    amount INTEGER NOT NULL,
                    currency TEXT NOT NULL,
                    status TEXT NOT NULL,
                    processor TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            conn.commit()

    def add_payout(self, payout_id: str, user_id: str, amount: int, currency: str,
                   status: str, processor: str) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO payouts (id, user_id, amount, currency, status, processor)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (payout_id, user_id, amount, currency, status, processor),
            )
            conn.commit()

    def update_status(self, payout_id: str, status: str) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "UPDATE payouts SET status = ? WHERE id = ?",
                (status, payout_id),
            )
            conn.commit()

    def get_payout(self, payout_id: str) -> Optional[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.execute(
                "SELECT id, user_id, amount, currency, status, processor, created_at "
                "FROM payouts WHERE id = ?",
                (payout_id,),
            )
            row = cur.fetchone()
            if row:
                keys = ["id", "user_id", "amount", "currency", "status", "processor", "created_at"]
                return dict(zip(keys, row))
            return None
