"""Usage event ledger with optional Kafka streaming."""

from dataclasses import dataclass, asdict
from datetime import datetime, timedelta, UTC
from typing import Optional, Iterable, Any
import json
import sqlite3

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
    ):
        self.db_path = db_path
        self.kafka_topic = kafka_topic
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
            conn.commit()

    def add_event(self, event: UsageEvent) -> None:
        """Insert event and optionally stream to Kafka."""
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
