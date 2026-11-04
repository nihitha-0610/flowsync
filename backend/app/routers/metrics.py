"""FlowSync - Tumbling Window Aggregation Metrics Endpoints."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Query

from app.database import execute_query

router = APIRouter(prefix="/api/v1/metrics", tags=["Windowed Metrics"])


@router.get("/windows")
def get_windowed_metrics(
    limit: int = Query(50, ge=1, le=500),
    device_id: Optional[str] = Query(None),
) -> List[Dict[str, Any]]:
    """Retrieve Spark streaming tumbling window aggregated metrics."""
    if device_id:
        sql = """
            SELECT id, window_start, window_end, device_id, device_type,
                   event_count, avg_temperature, max_temperature,
                   avg_vibration, max_vibration, avg_pressure, created_at
            FROM pipeline_windowed_metrics
            WHERE device_id = %s
            ORDER BY window_start DESC
            LIMIT %s;
        """
        return execute_query(sql, (device_id, limit))
    else:
        sql = """
            SELECT id, window_start, window_end, device_id, device_type,
                   event_count, avg_temperature, max_temperature,
                   avg_vibration, max_vibration, avg_pressure, created_at
            FROM pipeline_windowed_metrics
            ORDER BY window_start DESC
            LIMIT %s;
        """
        return execute_query(sql, (limit,))

