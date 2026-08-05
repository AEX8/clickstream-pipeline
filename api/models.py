from datetime import datetime
from sqlalchemy import func
from sqlalchemy.orm import Mapped, mapped_column
from database import Base


class EventRaw(Base):
    __tablename__ = "events_raw"

    event_id: Mapped[str] = mapped_column(primary_key=True)  # uuid, dedupe key for idempotent writes
    session_id: Mapped[str] = mapped_column(index=True)
    user_id: Mapped[str] = mapped_column(index=True)
    event_type: Mapped[str]  # page_view | click | add_to_cart | checkout_start | checkout_complete
    page_url: Mapped[str]
    referrer: Mapped[str | None]
    device: Mapped[str]
    user_agent: Mapped[str | None]
    event_timestamp: Mapped[datetime]  # when it happened, per the producer
    ingested_at: Mapped[datetime] = mapped_column(server_default=func.now())  # when postgres saw it

class Session(Base):
    __tablename__ = "sessions"

    session_id: Mapped[str] = mapped_column(primary_key=True)
    user_id: Mapped[str] = mapped_column(index=True)
    device: Mapped[str]
    started_at: Mapped[datetime]
    last_seen_at: Mapped[datetime]
    entry_page: Mapped[str]
    exit_page: Mapped[str]
    event_count: Mapped[int] = mapped_column(default=0)
    reached_checkout: Mapped[bool] = mapped_column(default=False)  # simple funnel flag
    last_processed_event_id: Mapped[str | None]  # dedupe guard for idempotent consumer restarts

class ActiveUsersMetric(Base):
    __tablename__ = "active_users_metrics"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    window_start: Mapped[datetime] = mapped_column(index=True)
    window_end: Mapped[datetime]
    active_user_count: Mapped[int]
    event_count: Mapped[int]

class FunnelMetric(Base):
    __tablename__ = "funnel_metrics"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    window_start: Mapped[datetime] = mapped_column(index=True)
    window_end: Mapped[datetime]
    event_type: Mapped[str]
    count: Mapped[int]