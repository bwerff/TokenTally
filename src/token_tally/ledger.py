import sqlite3
from datetime import datetime, UTC
from typing import Optional, Dict, Any

from . import fx
from . import markup

try:
    from opentelemetry import trace
except Exception:  # pragma: no cover - optional

    class _DummySpan:
        def __enter__(self):
            return self

        def __exit__(self, *exc: object) -> None:
            pass

        def set_attribute(self, *args: object, **kwargs: object) -> None:
            pass

    class _DummyTracer:
        def start_as_current_span(self, name: str) -> _DummySpan:
            return _DummySpan()

    class _TraceModule:
        def get_tracer(self, name: str | None = None) -> _DummyTracer:
            return _DummyTracer()

    trace = _TraceModule()  # type: ignore

tracer = trace.get_tracer(__name__)


class Ledger:
    """Simple SQLite ledger for payouts and usage events."""

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

            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS usage_events (
                    id TEXT PRIMARY KEY,
                    customer_id TEXT NOT NULL,
                    feature TEXT NOT NULL,
                    units INTEGER NOT NULL,
                    unit_cost REAL NOT NULL,
                    ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    stripe_status TEXT NOT NULL DEFAULT 'pending',
                    stripe_record_id TEXT,
                    invoice_cycle TEXT NOT NULL
                )
                """
            )

            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS invoices (
                    id TEXT PRIMARY KEY,
                    customer_id TEXT NOT NULL,
                    cycle TEXT NOT NULL,
                    amount REAL NOT NULL
                )
                """
            )

            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS credit_notes (
                    id TEXT PRIMARY KEY,
                    invoice_id TEXT NOT NULL,
                    amount REAL NOT NULL,
                    description TEXT
                )
                """
            )

            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS budgets (
                    customer_id TEXT PRIMARY KEY,
                    monthly_limit REAL NOT NULL
                )
                """
            )

            conn.commit()

    def add_payout(
        self,
        payout_id: str,
        user_id: str,
        amount: int,
        currency: str,
        status: str,
        processor: str,
    ) -> None:
        with tracer.start_as_current_span("Ledger.add_payout") as span:
            if span:
                try:
                    span.set_attribute("payout_id", payout_id)
                except Exception:  # pragma: no cover - dummy span
                    pass
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
        with tracer.start_as_current_span("Ledger.update_status") as span:
            if span:
                try:
                    span.set_attribute("payout_id", payout_id)
                except Exception:  # pragma: no cover - dummy span
                    pass
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
                keys = [
                    "id",
                    "user_id",
                    "amount",
                    "currency",
                    "status",
                    "processor",
                    "created_at",
                ]
                return dict(zip(keys, row))
            return None

    # Usage event helpers -------------------------------------------------

    def add_usage_event(
        self,
        event_id: str,
        customer_id: str,
        feature: str,
        units: int,
        unit_cost: float,
        invoice_cycle: str,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        currency: str = "USD",
        fx_rates: Optional[dict] = None,
        ts: Optional[datetime] = None,
        markup_db_path: Optional[str] = None,
    ) -> None:
        with tracer.start_as_current_span("Ledger.add_usage_event") as span:
            if span:
                try:
                    span.set_attribute("event_id", event_id)
                except Exception:  # pragma: no cover - dummy span
                    pass
            ts = ts or datetime.now(UTC)
            markup_rule = None
            if provider and model:
                rule = markup.get_effective_markup(
                    provider,
                    model,
                    ts.isoformat(),
                    db_path=markup_db_path or "markup_rules.db",
                )
                markup_rule = rule["markup"] if rule else 0.0
            else:
                markup_rule = 0.0

            final_cost = unit_cost * (1 + markup_rule)
            if currency != "USD" and fx_rates:
                final_cost = fx.convert(final_cost, currency, "USD", fx_rates)

            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO usage_events (
                        id, customer_id, feature, units, unit_cost, invoice_cycle
                    )
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (event_id, customer_id, feature, units, final_cost, invoice_cycle),
                )
                conn.commit()

    def get_pending_usage_events(self):
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.execute(
                "SELECT id, customer_id, feature, units, unit_cost, ts, invoice_cycle "
                "FROM usage_events WHERE stripe_status = 'pending'"
            )
            keys = [
                "id",
                "customer_id",
                "feature",
                "units",
                "unit_cost",
                "ts",
                "invoice_cycle",
            ]
            return [dict(zip(keys, row)) for row in cur.fetchall()]

    def mark_usage_synced(self, event_id: str, record_id: str) -> None:
        with tracer.start_as_current_span("Ledger.mark_usage_synced") as span:
            if span:
                try:
                    span.set_attribute("event_id", event_id)
                except Exception:  # pragma: no cover - dummy span
                    pass
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    "UPDATE usage_events SET stripe_status = 'synced', stripe_record_id = ? WHERE id = ?",
                    (record_id, event_id),
                )
                conn.commit()

    def get_usage_events_by_cycle(self, cycle: str):
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.execute(
                "SELECT customer_id, units, unit_cost FROM usage_events WHERE invoice_cycle = ?",
                (cycle,),
            )
            keys = ["customer_id", "units", "unit_cost"]
            return [dict(zip(keys, row)) for row in cur.fetchall()]

    def get_usage_events_by_range(self, start: str, end: str):
        """Return usage events between ``start`` and ``end`` dates (inclusive)."""
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.execute(
                """
                SELECT customer_id, feature, units, unit_cost, ts
                FROM usage_events
                WHERE date(ts) >= date(?) AND date(ts) <= date(?)
                """,
                (start, end),
            )
            keys = ["customer_id", "feature", "units", "unit_cost", "ts"]
            return [dict(zip(keys, row)) for row in cur.fetchall()]

    def create_invoice(
        self, invoice_id: str, customer_id: str, cycle: str, amount: float
    ) -> None:
        with tracer.start_as_current_span("Ledger.create_invoice") as span:
            if span:
                try:
                    span.set_attribute("invoice_id", invoice_id)
                except Exception:  # pragma: no cover - dummy span
                    pass
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    "INSERT OR REPLACE INTO invoices (id, customer_id, cycle, amount) VALUES (?, ?, ?, ?)",
                    (invoice_id, customer_id, cycle, amount),
                )
                conn.commit()

    def create_credit_note(
        self, note_id: str, invoice_id: str, amount: float, description: str
    ) -> None:
        with tracer.start_as_current_span("Ledger.create_credit_note") as span:
            if span:
                try:
                    span.set_attribute("note_id", note_id)
                except Exception:  # pragma: no cover - dummy span
                    pass
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    "INSERT OR REPLACE INTO credit_notes (id, invoice_id, amount, description) VALUES (?, ?, ?, ?)",
                    (note_id, invoice_id, amount, description),
                )
                conn.commit()

    # Budget helpers ------------------------------------------------------

    def set_budget(self, customer_id: str, monthly_limit: float) -> None:
        """Insert or update a monthly budget for a customer."""
        with tracer.start_as_current_span("Ledger.set_budget") as span:
            if span:
                try:
                    span.set_attribute("customer_id", customer_id)
                except Exception:  # pragma: no cover - dummy span
                    pass
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    "INSERT OR REPLACE INTO budgets (customer_id, monthly_limit) VALUES (?, ?)",
                    (customer_id, monthly_limit),
                )
                conn.commit()

    def get_budget(self, customer_id: str) -> Optional[float]:
        """Return the monthly limit for the given customer, if set."""
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.execute(
                "SELECT monthly_limit FROM budgets WHERE customer_id = ?",
                (customer_id,),
            )
            row = cur.fetchone()
            return float(row[0]) if row else None

    def list_budgets(self) -> list[tuple[str, float]]:
        """Return ``[(customer_id, monthly_limit), ...]`` for all budgets."""
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.execute("SELECT customer_id, monthly_limit FROM budgets")
            return [(row[0], float(row[1])) for row in cur.fetchall()]
