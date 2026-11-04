"""Unit tests for FlowSync Corruption & Chaos Injector."""

import pytest
from ingestion.corruption import CorruptionInjector, CorruptionKind


@pytest.fixture
def baseline_event():
    return {
        "event_id": "11111111-2222-3333-4444-555555555555",
        "device_id": "DEV-0005",
        "facility_id": "FAC-02",
        "timestamp": "2026-10-30T12:00:00.000Z",
        "temperature": 55.0,
        "vibration": 2.5,
        "pressure": 40.0,
        "flow_rate": 180.0,
        "power_consumption": 30.0,
        "status_code": "OK",
        "location": "Zone-B",
    }


def test_corruption_kinds_execution(baseline_event):
    injector = CorruptionInjector(seed=42)

    for kind in list(CorruptionKind):
        corrupted, applied_kind, reason = injector.inject(baseline_event, kind=kind)
        assert applied_kind == kind
        assert isinstance(reason, str) and len(reason) > 0

        if kind == CorruptionKind.MISSING_FIELD:
            assert len(corrupted.keys()) < len(baseline_event.keys())
        elif kind == CorruptionKind.NULL_VALUE:
            assert any(v is None for v in corrupted.values())
        elif kind == CorruptionKind.WRONG_TYPE:
            assert any(isinstance(v, str) and "INVALID" in v for v in corrupted.values())
        elif kind == CorruptionKind.OUT_OF_RANGE:
            assert corrupted["temperature"] == 9999.0 or corrupted["vibration"] == -50.0 or corrupted["pressure"] == 500.0
        elif kind == CorruptionKind.BAD_TIMESTAMP:
            assert "Z" not in corrupted["timestamp"] or "NOT_A_TIMESTAMP" in corrupted["timestamp"] or "/" in corrupted["timestamp"]
        elif kind == CorruptionKind.BAD_DEVICE_ID:
            assert not corrupted["device_id"].startswith("DEV-") or len(corrupted["device_id"]) != 8
        elif kind == CorruptionKind.BAD_STATUS:
            assert corrupted["status_code"] not in ["OK", "WARNING", "CRITICAL", "MAINTENANCE"]
        elif kind == CorruptionKind.TRUNCATED_JSON:
            assert isinstance(corrupted, str)
        elif kind == CorruptionKind.LATE:
            assert "Z" in corrupted["timestamp"]

