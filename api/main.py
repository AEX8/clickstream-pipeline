"""
Serves clickstream metrics computed by the aggregator consumer.
Read-only — this API doesn't write anything, all writes happen
via the Kafka consumers.
"""

import asyncio
import json
from fastapi import FastAPI, Depends, WebSocket, WebSocketDisconnect
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

@app.websocket("/ws/metrics")
async def websocket_metrics(websocket: WebSocket):
    await websocket.accept()
    last_sent_window = None

    try:
        while True:
            db = next(get_db())
            try:
                metric = (
                    db.query(ActiveUsersMetric)
                    .order_by(desc(ActiveUsersMetric.window_start))
                    .first()
                )

                # only push if this is a window we haven't already sent — avoids spamming the client with identical data every poll
                if metric and metric.window_start != last_sent_window:
                    last_sent_window = metric.window_start

                    funnel_rows = (
                        db.query(FunnelMetric)
                        .filter(FunnelMetric.window_start == metric.window_start)
                        .all()
                    )

                    payload = {
                        "active_user_count": metric.active_user_count,
                        "event_count": metric.event_count,
                        "window_start": metric.window_start.isoformat(),
                        "window_end": metric.window_end.isoformat(),
                        "funnel": {row.event_type: row.count for row in funnel_rows},
                    }
                    await websocket.send_text(json.dumps(payload))
            finally:
                db.close()

            await asyncio.sleep(2)  # poll interval — check for a new window every 2s

    except WebSocketDisconnect:
        print("client disconnected from /ws/metrics")