"""
Serves clickstream metrics computed by the aggregator consumer.
Read-only — this API doesn't write anything, all writes happen
via the Kafka consumers.
"""

from fastapi import FastAPI, Depends
from sqlalchemy import desc
from sqlalchemy.orm import Session as DBSession

from database import get_db
from models import ActiveUsersMetric, FunnelMetric

app = FastAPI(title="Clickstream Analytics API")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/metrics/active-users/latest")
def latest_active_users(db: DBSession = Depends(get_db)):
    metric = (
        db.query(ActiveUsersMetric)
        .order_by(desc(ActiveUsersMetric.window_start))
        .first()
    )
    if metric is None:
        return {"active_user_count": 0, "event_count": 0, "window_start": None}

    return {
        "active_user_count": metric.active_user_count,
        "event_count": metric.event_count,
        "window_start": metric.window_start,
        "window_end": metric.window_end,
    }


@app.get("/metrics/funnel/latest")
def latest_funnel(db: DBSession = Depends(get_db)):
    latest_window = (
        db.query(FunnelMetric.window_start)
        .order_by(desc(FunnelMetric.window_start))
        .first()
    )
    if latest_window is None:
        return {"window_start": None, "steps": {}}

    rows = (
        db.query(FunnelMetric)
        .filter(FunnelMetric.window_start == latest_window[0])
        .all()
    )
    return {
        "window_start": latest_window[0],
        "steps": {row.event_type: row.count for row in rows},
    }