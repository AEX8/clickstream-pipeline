"""
Maintains live session state as events arrive. Unlike raw_writer,
which just appends, this one does read-then-update: each event either
creates a new session row or updates an existing one in place.
"""

import json
import os
import sys
from datetime import datetime

from dotenv import load_dotenv
from kafka import KafkaConsumer

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "api"))

from database import SessionLocal  # noqa: E402
from models import Session  # noqa: E402

load_dotenv()

TOPIC = "raw_events"
BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9094")
GROUP_ID = "sessionizer-group"  # own consumer group — independent of raw_writer's offsets


def build_consumer() -> KafkaConsumer:
    return KafkaConsumer(
        TOPIC,
        bootstrap_servers=BOOTSTRAP_SERVERS,
        group_id=GROUP_ID,
        value_deserializer=lambda v: json.loads(v.decode("utf-8")),
        key_deserializer=lambda k: k.decode("utf-8") if k else None,
        auto_offset_reset="earliest",
        enable_auto_commit=False,
    )


def upsert_session(db, event: dict) -> None:
    session_id = event["session_id"]
    event_time = datetime.fromisoformat(event["timestamp"])

    session = db.get(Session, session_id)

    if session is None:
        # first event we've seen for this session — create it
        session = Session(
            session_id=session_id,
            user_id=event["user_id"],
            device=event["device"],
            started_at=event_time,
            last_seen_at=event_time,
            entry_page=event["page_url"],
            exit_page=event["page_url"],
            event_count=1,
            reached_checkout=(event["event_type"] == "checkout_complete"),
        )
        db.add(session)
    else:
        # session already exists — update the rolling fields
        session.last_seen_at = event_time
        session.exit_page = event["page_url"]
        session.event_count += 1
        if event["event_type"] == "checkout_complete":
            session.reached_checkout = True

    db.commit()


def run() -> None:
    consumer = build_consumer()
    db = SessionLocal()

    print(f"sessionizer listening on '{TOPIC}' as group '{GROUP_ID}'... Ctrl+C to stop.")
    try:
        for message in consumer:
            event = message.value
            upsert_session(db, event)
            consumer.commit()
            print(f"session {event['session_id'][:8]}... now at {event['event_type']}")
    except KeyboardInterrupt:
        print("Stopping sessionizer...")
    finally:
        db.close()
        consumer.close()


if __name__ == "__main__":
    run()