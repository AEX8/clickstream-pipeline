"""
Simulates realistic web traffic and publishes events to Kafka.
"""

import json
import random
import time
import uuid
from datetime import datetime, timezone

from faker import Faker
from kafka import KafkaProducer

fake = Faker()

TOPIC = "raw_events"
BOOTSTRAP_SERVERS = "localhost:9094"  # matches PLAINTEXT_HOST listener from docker-compose

PAGES = [
    "/", "/products", "/products/1", "/products/2", "/products/3",
    "/search", "/cart", "/checkout", "/about", "/blog",
]

ARCHETYPES = ["bounce", "browse_only", "cart_abandoner", "converter"]
ARCHETYPE_WEIGHTS_DESKTOP = [0.30, 0.35, 0.20, 0.15]
ARCHETYPE_WEIGHTS_MOBILE = [0.50, 0.35, 0.10, 0.05]


def build_producer() -> KafkaProducer:
    return KafkaProducer(
        bootstrap_servers=BOOTSTRAP_SERVERS,
        key_serializer=lambda k: k.encode("utf-8"),
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
    )


def pick_archetype(device: str) -> str:
    weights = ARCHETYPE_WEIGHTS_MOBILE if device == "mobile" else ARCHETYPE_WEIGHTS_DESKTOP
    return random.choices(ARCHETYPES, weights=weights, k=1)[0]


def build_event_sequence(archetype: str) -> list[str]:
    """Maps an archetype to the ordered list of event_types a session will fire."""
    browse_pages = random.randint(1, 4)

    if archetype == "bounce":
        return ["page_view"]

    if archetype == "browse_only":
        return ["page_view"] * browse_pages

    if archetype == "cart_abandoner":
        return ["page_view"] * browse_pages + ["add_to_cart"]

    # converter
    return ["page_view"] * browse_pages + ["add_to_cart", "checkout_start", "checkout_complete"]


def simulate_session(producer: KafkaProducer) -> None:
    session_id = str(uuid.uuid4())
    user_id = str(uuid.uuid4())
    device = random.choice(["desktop", "mobile"])
    user_agent = fake.user_agent()

    archetype = pick_archetype(device)
    event_types = build_event_sequence(archetype)

    referrer = random.choice(["/search", "https://google.com", "https://instagram.com", None])
    current_page = "/"

    for event_type in event_types:
        # pick a page for this event — checkout events pin to checkout pages,
        # everything else wanders around the catalog
        if event_type == "add_to_cart":
            current_page = "/cart"
        elif event_type in ("checkout_start", "checkout_complete"):
            current_page = "/checkout"
        else:
            current_page = random.choice(PAGES)

        event = {
            "event_id": str(uuid.uuid4()),
            "session_id": session_id,
            "user_id": user_id,
            "event_type": event_type,
            "page_url": current_page,
            "referrer": referrer,
            "device": device,
            "user_agent": user_agent,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        # key by session_id so kafka guarantees all events for this
        # session land on the same partition, in order
        producer.send(TOPIC, key=session_id, value=event)
        print(f"[{device}] {archetype} → {event_type} @ {current_page}")

        # realistic gap between actions within a session
        time.sleep(random.uniform(1, 4))

    referrer = None  # only the entry event carries a referrer, rest is direct navigation


def run(sessions_per_minute: int = 10) -> None:
    producer = build_producer()
    delay_between_sessions = 60 / sessions_per_minute

    print(f"Starting traffic simulator — ~{sessions_per_minute} sessions/min. Ctrl+C to stop.")
    try:
        while True:
            simulate_session(producer)
            time.sleep(delay_between_sessions)
    except KeyboardInterrupt:
        print("Stopping simulator...")
    finally:
        producer.flush()
        producer.close()


if __name__ == "__main__":
    run(sessions_per_minute=10)