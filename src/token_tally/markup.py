import sqlite3
from typing import Optional, Dict, List, Any


class MarkupRuleStore:
    """SQLite-backed store for markup rules."""

    def __init__(self, db_path: str = "markup_rules.db"):
        self.db_path = db_path
        self._ensure_table()

    def load_rules(self, rules: List[Dict[str, Any]]) -> None:
        """Bulk insert rules represented as dictionaries."""
        for rule in rules:
            self.create_rule(
                rule["id"],
                rule["provider"],
                rule["model"],
                float(rule["markup"]),
                rule["effective_date"],
            )

    def load_from_dsl(self, text: str) -> None:
        """Parse DSL text and load resulting rules."""
        from .pricing_dsl import parse_pricing_dsl

        self.load_rules(parse_pricing_dsl(text))

    def _ensure_table(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS markup_rules (
                    id TEXT PRIMARY KEY,
                    provider TEXT NOT NULL,
                    model TEXT NOT NULL,
                    markup REAL NOT NULL,
                    effective_date TEXT NOT NULL
                )
                """
            )
            conn.commit()

    def create_rule(
        self,
        rule_id: str,
        provider: str,
        model: str,
        markup: float,
        effective_date: str,
    ) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO markup_rules
                    (id, provider, model, markup, effective_date)
                VALUES (?, ?, ?, ?, ?)
                """,
                (rule_id, provider, model, markup, effective_date),
            )
            conn.commit()

    def get_rule(self, rule_id: str) -> Optional[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.execute(
                """
                SELECT id, provider, model, markup, effective_date
                FROM markup_rules WHERE id = ?
                """,
                (rule_id,),
            )
            row = cur.fetchone()
        if row:
            keys = ["id", "provider", "model", "markup", "effective_date"]
            return dict(zip(keys, row))
        return None

    def list_rules(self) -> List[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.execute(
                "SELECT id, provider, model, markup, effective_date FROM markup_rules"
            )
            rows = cur.fetchall()
        keys = ["id", "provider", "model", "markup", "effective_date"]
        return [dict(zip(keys, row)) for row in rows]

    def update_rule(self, rule_id: str, **updates: Any) -> None:
        fields = []
        values = []
        for key, value in updates.items():
            if key not in {"provider", "model", "markup", "effective_date"}:
                continue
            fields.append(f"{key} = ?")
            values.append(value)
        if not fields:
            return
        values.append(rule_id)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                f"UPDATE markup_rules SET {', '.join(fields)} WHERE id = ?",
                values,
            )
            conn.commit()

    def delete_rule(self, rule_id: str) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM markup_rules WHERE id = ?", (rule_id,))
            conn.commit()


def get_effective_markup(
    provider: str,
    model: str,
    ts: str,
    db_path: str = "markup_rules.db",
) -> Optional[Dict[str, Any]]:
    """Return the markup rule active at ``ts`` for the given provider/model."""

    with sqlite3.connect(db_path) as conn:
        cur = conn.execute(
            """
            SELECT id, provider, model, markup, effective_date
            FROM markup_rules
            WHERE provider = ? AND model = ? AND effective_date <= ?
            ORDER BY effective_date DESC
            LIMIT 1
            """,
            (provider, model, ts),
        )
        row = cur.fetchone()

    if row:
        keys = ["id", "provider", "model", "markup", "effective_date"]
        return dict(zip(keys, row))
    return None
