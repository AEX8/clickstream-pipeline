"""
consumers/raw_writer.py

Reads every event off the raw_events topic and persists it, untouched,
into events_raw. This is the "full fidelity log" consumer — source of
truth for reprocessing if anything downstream ever needs a redo.
"""

import json
import os
import sys
from datetime import datetime

from dotenv import load_dotenv
from kafka import KafkaConsumer
from sqlalchemy.dialects.postgresql import insert

# reuse the same models/database setup as the api, instead of duplicating schema
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "api"))

from database import SessionLocal  # noqa: E402
from models import EventRaw  # noqa: E402

load_dotenv()

TOPIC = "raw_events"
BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9094")
GROUP_ID = "raw-writer-group"  # this consumer's identity for offset tracking


def build_consumer() -> KafkaConsumer:
    return KafkaConsumer(
        TOPIC,
        bootstrap_servers=BOOTSTRAP_SERVERS,
        group_id=GROUP_ID,
        value_deserializer=lambda v: json.loads(v.decode("utf-8")),
        key_deserializer=lambda k: k.decode("utf-8") if k else None,
        auto_offset_reset="earliest",  # if this is a brand new group, start from the beginning of the topic
        enable_auto_commit=False,  # we commit manually, only after a successful db write
    )


def write_event(db, event: dict) -> None:
    """
    Upsert on event_id — if this event was already written (e.g. we crashed
    right after writing but before committing the kafka offset, and got
    redelivered), this just no-ops instead of duplicating the row.
    That's what makes at-least-once delivery safe here.
    """
    stmt = insert(EventRaw).values(
        event_id=event["event_id"],
        session_id=event["session_id"],
        user_id=event["user_id"],
        event_type=event["event_type"],
        page_url=event["page_url"],
        referrer=event.get("referrer"),
        device=event["device"],
        user_agent=event.get("user_agent"),
        event_timestamp=datetime.fromisoformat(event["timestamp"]),
    )
    stmt = stmt.on_conflict_do_nothing(index_elements=["event_id"])
    db.execute(stmt)
    db.commit()


def run() -> None:
    consumer = build_consumer()
    db = SessionLocal()

    print(f"raw_writer listening on '{TOPIC}' as group '{GROUP_ID}'... Ctrl+C to stop.")
    try:
        for message in consumer:
            event = message.value
            write_event(db, event)

            # only commit the offset AFTER the db write succeeded —
            # if we crash between the write and this line, we'll just
            # reprocess this message next time, and the upsert makes that safe
            consumer.commit()

            print(f"wrote {event['event_type']} for session {event['session_id'][:8]}...")
    except KeyboardInterrupt:
        print("Stopping raw_writer...")
    finally:
        db.close()
        consumer.close()


if __name__ == "__main__":
    run()