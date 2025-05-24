from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime, UTC
from hashlib import sha256
from typing import List, Optional, Dict, Any


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
                    token_count INTEGER NOT NULL,
                    prev_hash TEXT
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
        ts = ts or datetime.now(UTC)
        prompt_hash = sha256(prompt.encode("utf-8")).hexdigest()
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.execute(
                "SELECT prev_hash FROM audit_events WHERE customer_id = ? ORDER BY ts DESC LIMIT 1",
                (customer_id,),
            )
            row = cur.fetchone()
            last_hash = row[0] if row else ""
            chain_hash = sha256((last_hash + prompt_hash).encode("utf-8")).hexdigest()
            conn.execute(
                """
                INSERT OR REPLACE INTO audit_events (
                    event_id, ts, customer_id, prompt_hash, token_count, prev_hash
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    event_id,
                    ts.isoformat(),
                    customer_id,
                    prompt_hash,
                    token_count,
                    chain_hash,
                ),
            )
            conn.commit()

    def list_events(self, customer_id: Optional[str] = None) -> List[Dict[str, Any]]:
        query = "SELECT event_id, ts, customer_id, prompt_hash, token_count, prev_hash FROM audit_events"
        params: tuple[str, ...] = ()
        if customer_id:
            query += " WHERE customer_id = ?"
            params = (customer_id,)
        query += " ORDER BY ts"
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.execute(query, params)
            rows = cur.fetchall()
        keys = [
            "event_id",
            "ts",
            "customer_id",
            "prompt_hash",
            "token_count",
            "prev_hash",
        ]
        return [dict(zip(keys, row)) for row in rows]

    def verify_chain(self, customer_id: Optional[str] = None) -> bool:
        """Return ``True`` if the hash chain is intact."""
        customers: List[str]
        with sqlite3.connect(self.db_path) as conn:
            if customer_id:
                customers = [customer_id]
            else:
                cur = conn.execute("SELECT DISTINCT customer_id FROM audit_events")
                customers = [row[0] for row in cur.fetchall()]
            for cust in customers:
                cur = conn.execute(
                    "SELECT prompt_hash, prev_hash FROM audit_events WHERE customer_id = ? ORDER BY ts",
                    (cust,),
                )
                rows = cur.fetchall()
                prev = ""
                for prompt_hash, stored_hash in rows:
                    expected = sha256((prev + prompt_hash).encode("utf-8")).hexdigest()
                    if stored_hash != expected:
                        return False
                    prev = stored_hash
        return True
