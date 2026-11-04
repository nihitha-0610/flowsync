"""FlowSync - AI Anomaly Detections Endpoints."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Query

from app.database import execute_query

router = APIRouter(prefix="/api/v1/anomalies", tags=["Anomaly Detections"])


@router.get("")
def get_anomalies(
    limit: int = Query(50, ge=1, le=500),
    device_id: Optional[str] = Query(None),
) -> List[Dict[str, Any]]:
    """Retrieve Isolation Forest detected anomalies with explainability attribution."""
    if device_id:
        sql = """
            SELECT id, anomaly_id, event_id, device_id, timestamp,
                   anomaly_score, confidence, is_anomaly, primary_driver,
                   feature_contributions, detected_at
            FROM anomaly_detections
            WHERE device_id = %s
            ORDER BY timestamp DESC
            LIMIT %s;
        """
        return execute_query(sql, (device_id, limit))
    else:
        sql = """
            SELECT id, anomaly_id, event_id, device_id, timestamp,
                   anomaly_score, confidence, is_anomaly, primary_driver,
                   feature_contributions, detected_at
            FROM anomaly_detections
            ORDER BY timestamp DESC
            LIMIT %s;
        """
        return execute_query(sql, (limit,))

