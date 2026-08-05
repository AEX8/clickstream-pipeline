"""
Buffers events in-memory for a fixed tumbling window (default 60s),
then flushes aggregated counts to Postgres and starts a fresh window.
This is plain-Python windowing — the simplest correct implementation.
Kafka Streams / Flink would be the natural next step if this needed
to scale beyond a single process.
"""

import json
import os
import sys
import time
from datetime import datetime, timezone

from dotenv import load_dotenv
from kafka import KafkaConsumer

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "api"))

from database import SessionLocal  # noqa: E402
from models import ActiveUsersMetric, FunnelMetric  # noqa: E402

load_dotenv()

TOPIC = "raw_events"
BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9094")
GROUP_ID = "aggregator-group"
WINDOW_SECONDS = 60


def build_consumer() -> KafkaConsumer:
    return KafkaConsumer(
        TOPIC,
        bootstrap_servers=BOOTSTRAP_SERVERS,
        group_id=GROUP_ID,
        value_deserializer=lambda v: json.loads(v.decode("utf-8")),
        key_deserializer=lambda k: k.decode("utf-8") if k else None,
        auto_offset_reset="earliest",
        enable_auto_commit=False,
        consumer_timeout_ms=1000,  # so the for-loop below doesn't block forever — lets us check the window timer
    )


class WindowBuffer:
    """Holds everything we're counting for the current window."""

    def __init__(self):
        self.window_start = datetime.now(timezone.utc)
        self.active_user_ids: set[str] = set()
        self.event_count = 0
        self.funnel_counts: dict[str, int] = {}

    def add(self, event: dict) -> None:
        self.active_user_ids.add(event["user_id"])
        self.event_count += 1
        event_type = event["event_type"]
        self.funnel_counts[event_type] = self.funnel_counts.get(event_type, 0) + 1


def flush_window(db, buffer: WindowBuffer) -> None:
    window_end = datetime.now(timezone.utc)

    db.add(ActiveUsersMetric(
        window_start=buffer.window_start,
        window_end=window_end,
        active_user_count=len(buffer.active_user_ids),
        event_count=buffer.event_count,
    ))

    for event_type, count in buffer.funnel_counts.items():
        db.add(FunnelMetric(
            window_start=buffer.window_start,
            window_end=window_end,
            event_type=event_type,
            count=count,
        ))

    db.commit()
    print(
        f"[flushed] {buffer.window_start.strftime('%H:%M:%S')} - {window_end.strftime('%H:%M:%S')} "
        f"| active_users={len(buffer.active_user_ids)} | events={buffer.event_count} "
        f"| funnel={buffer.funnel_counts}"
    )


def run() -> None:
    consumer = build_consumer()
    db = SessionLocal()
    buffer = WindowBuffer()

    print(f"aggregator listening on '{TOPIC}' as group '{GROUP_ID}', {WINDOW_SECONDS}s windows... Ctrl+C to stop.")
    try:
        while True:
            # consumer_timeout_ms means this loop exits (not blocks) if no
            # messages arrive within 1s, so we always get back here to check
            # whether the window has expired, even during quite periods
            for message in consumer:
                buffer.add(message.value)
                consumer.commit()

            elapsed = (datetime.now(timezone.utc) - buffer.window_start).total_seconds()
            if elapsed >= WINDOW_SECONDS:
                flush_window(db, buffer)
                buffer = WindowBuffer()

    except KeyboardInterrupt:
        print("Stopping aggregator...")
        if buffer.event_count > 0:
            flush_window(db, buffer)  # flush whatever's left so we don't lose a partial window
    finally:
        db.close()
        consumer.close()


if __name__ == "__main__":
    run()