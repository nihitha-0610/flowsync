"""FlowSync - Health & Readiness Endpoints."""

from __future__ import annotations

import os
from fastapi import APIRouter, Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
import psycopg

from app.database import DB_HOST, DB_NAME, DB_PORT, DB_USER, get_db_connection

router = APIRouter(tags=["Health & Monitoring"])


@router.get("/health")
def health_check():
    """Liveness probe returning service status."""
    return {"status": "healthy", "service": "flowsync-backend"}


@router.get("/ready")
def readiness_check():
    """Readiness probe testing database connection."""
    db_ok = False
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1;")
                db_ok = True
    except Exception as exc:
        db_error = str(exc)
        return {"status": "unready", "database": False, "error": db_error}

    return {"status": "ready", "database": True, "host": DB_HOST, "database_name": DB_NAME}


@router.get("/metrics")
def prometheus_metrics():
    """Prometheus exposition format metrics scraper."""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

