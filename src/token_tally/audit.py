from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime
from hashlib import sha256
from typing import List, Optional, Dict


@dataclass
class AuditEvent:
    event_id: str
    ts: datetime
    customer_id: str
    prompt_hash: str
    token_count: int


class AuditLog:
    """SQLite-backed audit log for hashed prompts."""

    def __init__(self, db_path: str = "audit_log.db"):
        self.db_path = db_path
        self._ensure_table()

    def _ensure_table(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS audit_events (
                    event_id TEXT PRIMARY KEY,
                    ts TEXT NOT NULL,
                    customer_id TEXT NOT NULL,
                    prompt_hash TEXT NOT NULL,
                    token_count INTEGER NOT NULL
                )
                """
            )
            conn.commit()

    def add_event(
        self,
        event_id: str,
        customer_id: str,
        prompt: str,
        token_count: int,
        ts: Optional[datetime] = None,
    ) -> None:
        ts = ts or datetime.utcnow()
        prompt_hash = sha256(prompt.encode("utf-8")).hexdigest()
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO audit_events (
                    event_id, ts, customer_id, prompt_hash, token_count
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (event_id, ts.isoformat(), customer_id, prompt_hash, token_count),
            )
            conn.commit()

    def list_events(self, customer_id: Optional[str] = None) -> List[Dict[str, any]]:
        query = "SELECT event_id, ts, customer_id, prompt_hash, token_count FROM audit_events"
        params: tuple[str, ...] = ()
        if customer_id:
            query += " WHERE customer_id = ?"
            params = (customer_id,)
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.execute(query, params)
            rows = cur.fetchall()
        keys = ["event_id", "ts", "customer_id", "prompt_hash", "token_count"]
        return [dict(zip(keys, row)) for row in rows]
