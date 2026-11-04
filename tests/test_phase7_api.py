"""FlowSync - Phase 7 FastAPI Backend HTTP Integration Tests.

Executes actual HTTP requests via FastAPI TestClient verifying status codes,
response headers, JSON schemas, route routing, and input validation.
"""

import os
import sys
import pytest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_root_endpoint():
    """Verify HTTP GET / returns 200 OK and pipeline service metadata."""
    res = client.get("/")
    assert res.status_code == 200
    data = res.json()
    assert data["service"] == "FlowSync Pipeline API"
    assert data["status"] == "operational"
    assert "version" in data


def test_health_and_readiness():
    """Verify HTTP GET /health and /ready probe behaviors."""
    # Health probe
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "healthy"

    # Readiness probe with mock db
    with patch("app.routers.health.get_db_connection") as mock_conn:
        mock_ctx = MagicMock()
        mock_conn.return_value.__enter__.return_value = mock_ctx
        res_ready = client.get("/ready")
        assert res_ready.status_code == 200
        assert res_ready.json()["status"] == "ready"
        assert res_ready.json()["database"] is True


def test_openapi_schema_endpoint():
    """Verify HTTP GET /openapi.json delivers complete OpenAPI specification."""
    res = client.get("/openapi.json")
    assert res.status_code == 200
    schema = res.json()
    assert "/api/v1/events/recent" in schema["paths"]
    assert "/api/v1/metrics/windows" in schema["paths"]
    assert "/api/v1/quality/runs" in schema["paths"]
    assert "/api/v1/anomalies" in schema["paths"]
    assert "/api/v1/ingest" in schema["paths"]


@patch("app.routers.events.execute_query")
def test_recent_events_http_endpoint(mock_exec):
    """Verify HTTP GET /api/v1/events/recent parameters and JSON response."""
    mock_exec.return_value = [
        {
            "event_id": "11111111-1111-1111-1111-111111111111",
            "device_id": "DEV-0001",
            "temperature": 60.5,
            "vibration": 3.2,
            "pressure": 45.0,
            "status_code": "OK",
        }
    ]
    res = client.get("/api/v1/events/recent?limit=10")
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 1
    assert data[0]["device_id"] == "DEV-0001"
    assert data[0]["temperature"] == 60.5


@patch("app.routers.anomalies.execute_query")
def test_anomalies_http_endpoint(mock_exec):
    """Verify HTTP GET /api/v1/anomalies returns scored anomaly records."""
    mock_exec.return_value = [
        {
            "anomaly_id": "aaaa-bbbb-cccc",
            "device_id": "DEV-0002",
            "primary_driver": "vibration",
            "confidence": 0.95,
            "anomaly_score": 0.88,
        }
    ]
    res = client.get("/api/v1/anomalies?limit=5")
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 1
    assert data[0]["primary_driver"] == "vibration"
    assert data[0]["confidence"] == 0.95


@patch("app.routers.metrics.execute_query")
def test_window_metrics_http_endpoint(mock_exec):
    """Verify HTTP GET /api/v1/metrics/windows returns aggregated streaming windows."""
    mock_exec.return_value = [
        {
            "id": 1,
            "window_start": "2026-10-30T12:00:00Z",
            "window_end": "2026-10-30T12:01:00Z",
            "device_type": "PUMP",
            "event_count": 120,
            "avg_temperature": 62.4,
        }
    ]
    res = client.get("/api/v1/metrics/windows?limit=10")
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 1
    assert data[0]["event_count"] == 120


@patch("app.routers.quality.execute_query")
def test_data_quality_runs_http_endpoint(mock_exec):
    """Verify HTTP GET /api/v1/quality/runs returns audit ledger history."""
    mock_exec.return_value = [
        {
            "run_id": "dq_test_run_1",
            "suite_name": "flowsync_canonical_suite",
            "total_records": 100,
            "valid_records": 98,
            "success_rate": 98.0,
            "execution_status": "SUCCESS",
        }
    ]
    res = client.get("/api/v1/quality/runs?limit=5")
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 1
    assert data[0]["success_rate"] == 98.0


@patch("app.routers.ingest.get_producer")
def test_manual_ingest_http_endpoint_success(mock_get_producer):
    """Verify HTTP POST /api/v1/ingest successfully accepts and validates telemetry."""
    mock_producer = MagicMock()
    mock_get_producer.return_value = mock_producer

    valid_payload = {
        "event_id": "12345678-1234-1234-1234-123456789abc",
        "device_id": "DEV-0001",
        "facility_id": "FAC-01",
        "timestamp": "2026-10-30T12:00:00Z",
        "location": "Sector-A",
        "temperature": 65.0,
        "vibration": 3.5,
        "pressure": 50.0,
        "flow_rate": 200.0,
        "power_consumption": 45.0,
        "status_code": "OK",
    }
    res = client.post("/api/v1/ingest", json=valid_payload)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert data["published_count"] == 1
    assert mock_producer.publish.called


def test_manual_ingest_http_endpoint_invalid_contract():
    """Verify HTTP POST /api/v1/ingest rejects contract-violating payloads."""
    invalid_payload = {
        "event_id": "not-a-valid-uuid",
        "device_id": "INVALID-DEVICE",
        "temperature": 999.0,  # exceeds physical boundary of 125.0
    }
    res = client.post("/api/v1/ingest", json=invalid_payload)
    assert res.status_code == 200
    data = res.json()
    # Pipeline isolates invalid records into errors list without crashing
    assert data["status"] in ("failed", "partial_failure")
    assert len(data["errors"]) > 0
