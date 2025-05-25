"""Usage event ledger with optional Kafka streaming."""

from dataclasses import dataclass, asdict
from datetime import datetime, timedelta, UTC
from typing import Optional, Iterable, Any
import json
import sqlite3

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

try:
    from kafka import KafkaProducer
except ImportError:  # pragma: no cover - kafka-python not installed
    KafkaProducer = None  # type: ignore

try:
    from clickhouse_driver import Client
except ImportError:  # pragma: no cover - clickhouse-driver not installed
    Client = None  # type: ignore


@dataclass
class UsageEvent:
    event_id: str
    ts: datetime
    customer_id: str
    provider: str
    model: str
    metric_type: str
    units: float
    unit_cost_usd: float


class UsageLedger:
    """Stores usage events in an append-only SQLite table."""

    def __init__(
        self,
        db_path: str = "usage_ledger.db",
        kafka_servers: Optional[Iterable[str]] = None,
        kafka_topic: str = "usage_events",
        dead_letter_topic: str = "dead_letter",
    ):
        self.db_path = db_path
        self.kafka_topic = kafka_topic
        self.dead_letter_topic = dead_letter_topic
        self.producer = None
        if kafka_servers and KafkaProducer:
            self.producer = KafkaProducer(
                bootstrap_servers=list(kafka_servers),
                value_serializer=lambda v: json.dumps(v).encode("utf-8"),
            )
        self._ensure_table()

    def _ensure_table(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS usage_events (
                    event_id TEXT PRIMARY KEY,
                    ts TEXT NOT NULL,
                    customer_id TEXT NOT NULL,
                    provider TEXT NOT NULL,
                    model TEXT NOT NULL,
                    metric_type TEXT NOT NULL,
                    units REAL NOT NULL,
                    unit_cost_usd REAL NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS dead_letter_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    raw TEXT NOT NULL,
                    error TEXT NOT NULL,
                    ts TEXT NOT NULL
                )
                """
            )
            conn.commit()

    def add_event(self, event: UsageEvent) -> None:
        """Insert event and optionally stream to Kafka."""
        with tracer.start_as_current_span("UsageLedger.add_event") as span:
            if span:
                try:
                    span.set_attribute("event_id", event.event_id)
                except Exception:  # pragma: no cover - dummy span
                    pass
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """
                    INSERT INTO usage_events (
                        event_id, ts, customer_id, provider, model,
                        metric_type, units, unit_cost_usd
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        event.event_id,
                        event.ts.isoformat(),
                        event.customer_id,
                        event.provider,
                        event.model,
                        event.metric_type,
                        event.units,
                        event.unit_cost_usd,
                    ),
                )
                conn.commit()
            if self.producer:
                self.producer.send(self.kafka_topic, asdict(event))
                self.producer.flush()

    def get_hourly_totals(self, hours: int) -> list[float]:
        """Return spend totals for the last ``hours`` hours."""
        end = datetime.now(UTC).replace(minute=0, second=0, microsecond=0)
        start = end - timedelta(hours=hours)
        totals = [0.0 for _ in range(hours)]
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.execute(
                "SELECT ts, units, unit_cost_usd FROM usage_events WHERE ts >= ? AND ts < ?",
                (start.isoformat(), end.isoformat()),
            )
            for ts_str, units, unit_cost in cur.fetchall():
                ts = datetime.fromisoformat(ts_str)
                idx = int((ts - start).total_seconds() // 3600)
                if 0 <= idx < hours:
                    totals[idx] += units * unit_cost
        return totals

    def _write_dead_letter(self, data: dict, error: str) -> None:
        raw = json.dumps(data)
        ts = datetime.now(UTC).isoformat()
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO dead_letter_events (raw, error, ts) VALUES (?, ?, ?)",
                (raw, error, ts),
            )
            conn.commit()
        if self.producer:
            self.producer.send(self.dead_letter_topic, {"raw": data, "error": error})
            self.producer.flush()

    def parse_event(self, data: dict) -> Optional[UsageEvent]:
        """Convert a dict to ``UsageEvent`` and log malformed input."""
        try:
            ts = data["ts"]
            if isinstance(ts, str):
                ts = datetime.fromisoformat(ts)
            if not isinstance(ts, datetime):
                raise ValueError("invalid ts")
            event = UsageEvent(
                event_id=str(data["event_id"]),
                ts=ts,
                customer_id=str(data["customer_id"]),
                provider=str(data["provider"]),
                model=str(data["model"]),
                metric_type=str(data["metric_type"]),
                units=float(data["units"]),
                unit_cost_usd=float(data["unit_cost_usd"]),
            )
            return event
        except (KeyError, TypeError, ValueError) as exc:  # pragma: no cover - defensive
            self._write_dead_letter(data, str(exc))
            return None


class ClickHouseUsageLedger:
    """Usage ledger backed by ClickHouse."""

    def __init__(
        self,
        host: str = "localhost",
        *,
        kafka_servers: Optional[Iterable[str]] = None,
        kafka_topic: str = "usage_events",
        **client_kwargs: Any,
    ) -> None:
        if Client is None:
            raise ImportError("clickhouse-driver not installed")
        self.client = Client(host=host, **client_kwargs)
        self.kafka_topic = kafka_topic
        self.producer = None
        if kafka_servers and KafkaProducer:
            self.producer = KafkaProducer(
                bootstrap_servers=list(kafka_servers),
                value_serializer=lambda v: json.dumps(v).encode("utf-8"),
            )
        self._ensure_table()

    def _ensure_table(self) -> None:
        self.client.execute(
            """
            CREATE TABLE IF NOT EXISTS usage_events (
                event_id String,
                ts DateTime,
                customer_id String,
                provider String,
                model String,
                metric_type String,
                units Float64,
                unit_cost_usd Float64
            )
            ENGINE = MergeTree()
            PARTITION BY toYYYYMMDD(ts)
            ORDER BY (ts, event_id)
            """
        )

    def add_event(self, event: UsageEvent) -> None:
        with tracer.start_as_current_span("ClickHouseUsageLedger.add_event") as span:
            if span:
                try:
                    span.set_attribute("event_id", event.event_id)
                except Exception:  # pragma: no cover - dummy span
                    pass
            self.client.execute(
                """
                INSERT INTO usage_events (
                    event_id, ts, customer_id, provider, model,
                    metric_type, units, unit_cost_usd
                ) VALUES
            """,
                [
                    (
                        event.event_id,
                        event.ts,
                        event.customer_id,
                        event.provider,
                        event.model,
                        event.metric_type,
                        event.units,
                        event.unit_cost_usd,
                    )
                ],
            )
            if self.producer:
                self.producer.send(self.kafka_topic, asdict(event))
                self.producer.flush()

    def get_hourly_totals(self, hours: int) -> list[float]:
        end = datetime.now(UTC).replace(minute=0, second=0, microsecond=0)
        start = end - timedelta(hours=hours)
        totals = [0.0 for _ in range(hours)]
        rows = self.client.execute(
            """
            SELECT ts, units, unit_cost_usd FROM usage_events
            WHERE ts >= %(start)s AND ts < %(end)s
            """,
            {"start": start, "end": end},
        )
        for ts, units, unit_cost in rows:
            idx = int((ts - start).total_seconds() // 3600)
            if 0 <= idx < hours:
                totals[idx] += units * unit_cost
        return totals
