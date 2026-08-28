<img src="./cs.png" width="300" alt="ClickStream-Pipeline" />

# Clickstream Analytics Pipeline

A real-time streaming data pipeline that ingests simulated web traffic, processes it through Kafka, and serves live metrics to a dashboard — active users, conversion funnel, and recent session activity, all updating in real time.

This is the streaming counterpart to my [batch ELT retail analytics pipeline](https://github.com/AEX8/retail-analytics-pipeline) — same "boring, industry-standard tools" philosophy, different paradigm: continuous event-driven processing instead of scheduled batch jobs.

## Why Kafka, and why these choices

- **Partitioned by `session_id`** — guarantees all events for one session land on the same partition, preserving order for sessionization without extra machinery.
- **KRaft mode, no Zookeeper** — Zookeeper is being phased out across the Kafka ecosystem; KRaft is the current production-standard broker mode.
- **Separate consumer groups per concern** (raw writer / sessionizer / aggregator) — each reads the full topic independently, and each can scale, fail, or restart without affecting the others.
- **At-least-once delivery, idempotent writes** — consumers commit their Kafka offset only *after* a successful DB write, and writes are upserts keyed on `event_id` (or a `last_processed_event_id` guard for the sessionizer). A crash-and-replay never produces duplicate data.
- **Plain Python consumers doing windowing**, not Kafka Streams/Flink — simplest correct implementation at this scale. The aggregator buffers events in memory for 60s, flushes aggregated counts, and resets. Kafka Streams/Flink would be the natural next step if this needed to scale beyond a single process.
- **New consumer groups start from the earliest offset** — the first time a group runs, it reads Kafka's full backlog before catching up to live traffic. Worth knowing when reading early metrics: the very first window can look inflated as it processes historical data, not a bug.

## Tech stack

- **Streaming:** Apache Kafka (KRaft mode)
- **Backend:** Python, FastAPI
- **Database:** PostgreSQL, SQLAlchemy 2.0, Alembic
- **Frontend:** React, TypeScript, Tailwind CSS, Vite
- **Infra:** Docker Compose

## Running locally

Seven terminals, in this order:

```bash
# 1. infra
docker compose up -d

# 2. producer
cd producer && source venv/bin/activate && python3 event_simulator.py

# 3-5. consumers (separate terminals)
cd consumers && source venv/bin/activate && python3 raw_writer.py
cd consumers && source venv/bin/activate && python3 sessionizer.py
cd consumers && source venv/bin/activate && python3 aggregator.py

# 6. api
cd api && source venv/bin/activate && uvicorn main:app --reload --port 8000

# 7. dashboard
cd dashboard && npm run dev
```

Dashboard: `http://localhost:5173` · API docs: `http://localhost:8000/docs` · Kafka UI: `http://localhost:8090`

## Design notes

- **API is read-only.** All writes happen through the Kafka consumers; the API only serves what's already been computed. This means the API can be scaled or restarted independently with zero risk to data integrity.
- **No auth on the API.** This is an internal analytics tool — in production it'd sit behind company SSO or a VPN, not its own auth layer.
- **WebSocket vs. REST is deliberate, not arbitrary.** The `/ws/metrics` WebSocket handles live aggregate metrics (pushed the moment a new window flushes). The recent-sessions table uses plain REST polling instead — no need to overload one socket with multiple message types for a table that only needs to refresh every few seconds.


## Roadmap

-  Docker Compose infra (Kafka KRaft + Postgres)
-  Postgres schema + Alembic migrations
-  Event producer with realistic session archetypes
-  Raw writer, sessionizer, windowed aggregator consumers
-  FastAPI REST + WebSocket layer
-  React live dashboard (metrics, funnel, sessions table)
