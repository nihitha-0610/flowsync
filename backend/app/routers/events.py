"""FlowSync - Events & Ingestion Query Endpoints."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Query

from app.database import execute_query, execute_scalar

router = APIRouter(prefix="/api/v1/events", tags=["Events Telemetry"])


@router.get("/recent")
def get_recent_events(
    limit: int = Query(50, ge=1, le=500),
    device_id: Optional[str] = Query(None),
) -> List[Dict[str, Any]]:
    """Retrieve recent valid telemetry events sorted by timestamp descending."""
    if device_id:
        sql = """
            SELECT id, event_id, timestamp, device_id, device_type, facility_id, location,
                   temperature, vibration, pressure, flow_rate, power_consumption,
                   status_code, source, processed_at
            FROM events_valid
            WHERE device_id = %s
            ORDER BY timestamp DESC
            LIMIT %s;
        """
        return execute_query(sql, (device_id, limit))
    else:
        sql = """
            SELECT id, event_id, timestamp, device_id, device_type, facility_id, location,
                   temperature, vibration, pressure, flow_rate, power_consumption,
                   status_code, source, processed_at
            FROM events_valid
            ORDER BY timestamp DESC
            LIMIT %s;
        """
        return execute_query(sql, (limit,))


@router.get("/invalid")
def get_invalid_events(
    limit: int = Query(50, ge=1, le=500),
) -> List[Dict[str, Any]]:
    """Retrieve quarantined records failing syntax, contract, or quality rules."""
    sql = """
        SELECT id, event_id, timestamp, raw_payload, raw_text,
               kafka_topic, kafka_partition, kafka_offset,
               failure_stage, failure_reason, failed_field, observed_value,
               violations, validation_run_id, quarantined_at
        FROM events_invalid
        ORDER BY quarantined_at DESC
        LIMIT %s;
    """
    return execute_query(sql, (limit,))


@router.get("/stats")
def get_events_statistics() -> Dict[str, Any]:
    """Summary metrics across valid events, quarantined records, and active devices."""
    valid_count = execute_scalar("SELECT COUNT(*) FROM events_valid;") or 0
    invalid_count = execute_scalar("SELECT COUNT(*) FROM events_invalid;") or 0
    device_count = execute_scalar("SELECT COUNT(DISTINCT device_id) FROM events_valid;") or 0
    anomaly_count = execute_scalar("SELECT COUNT(*) FROM anomaly_detections;") or 0
    recent_batch_count = execute_scalar("SELECT COUNT(*) FROM pipeline_batch_log WHERE status = 'SUCCESS';") or 0

    return {
        "valid_events_total": valid_count,
        "invalid_events_total": invalid_count,
        "active_devices_total": device_count,
        "anomalies_total": anomaly_count,
        "successful_microbatches": recent_batch_count,
    }

