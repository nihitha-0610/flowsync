"""Unit tests for FlowSync Canonical Telemetry Event Contract."""

import pytest
from pydantic import ValidationError

from core.event_contract import (
    CanonicalTelemetryEvent,
    PHYSICAL_RANGES,
    StatusCode,
)


def test_valid_canonical_event_creation():
    """Verify that a properly constructed event passes all validations."""
    event = CanonicalTelemetryEvent(
        event_id="550e8400-e29b-41d4-a716-446655440000",
        device_id="DEV-0001",
        facility_id="FAC-01",
        timestamp="2026-10-30T10:15:30.123Z",
        temperature=45.5,
        vibration=2.35,
        pressure=42.1,
        flow_rate=150.0,
        power_consumption=22.4,
        status_code=StatusCode.OK,
        location="Zone-A",
    )
    assert event.device_id == "DEV-0001"
    assert event.facility_id == "FAC-01"
    assert event.temperature == 45.5
    d = event.to_canonical_dict()
    assert d["status_code"] == "OK"
    assert "event_id" in d


def test_invalid_device_id_format():
    """Verify regex rejection on device_id."""
    with pytest.raises(ValidationError) as exc:
        CanonicalTelemetryEvent(
            device_id="DEVICE_001",  # Invalid pattern
            facility_id="FAC-01",
            timestamp="2026-10-30T10:15:30.123Z",
            temperature=50.0,
            vibration=1.0,
            pressure=30.0,
            flow_rate=100.0,
            power_consumption=20.0,
            status_code=StatusCode.OK,
            location="Zone-A",
        )
    assert "device_id" in str(exc.value)


def test_invalid_facility_id_format():
    """Verify regex rejection on facility_id."""
    with pytest.raises(ValidationError) as exc:
        CanonicalTelemetryEvent(
            device_id="DEV-0001",
            facility_id="FACILITY_A",  # Invalid pattern
            timestamp="2026-10-30T10:15:30.123Z",
            temperature=50.0,
            vibration=1.0,
            pressure=30.0,
            flow_rate=100.0,
            power_consumption=20.0,
            status_code=StatusCode.OK,
            location="Zone-A",
        )
    assert "facility_id" in str(exc.value)


def test_invalid_timestamp_missing_z():
    """Verify rejection of timestamps without UTC trailing 'Z'."""
    with pytest.raises(ValidationError) as exc:
        CanonicalTelemetryEvent(
            device_id="DEV-0001",
            facility_id="FAC-01",
            timestamp="2026-10-30T10:15:30.123",  # Missing 'Z'
            temperature=50.0,
            vibration=1.0,
            pressure=30.0,
            flow_rate=100.0,
            power_consumption=20.0,
            status_code=StatusCode.OK,
            location="Zone-A",
        )
    assert "timestamp" in str(exc.value)


def test_physical_range_boundaries():
    """Verify numerical sensor bounds rejection."""
    # Temperature out of bounds (> 125.0)
    with pytest.raises(ValidationError):
        CanonicalTelemetryEvent(
            device_id="DEV-0001",
            facility_id="FAC-01",
            timestamp="2026-10-30T10:15:30.123Z",
            temperature=200.0,
            vibration=1.0,
            pressure=30.0,
            flow_rate=100.0,
            power_consumption=20.0,
            status_code=StatusCode.OK,
            location="Zone-A",
        )

    # Vibration negative (< 0.0)
    with pytest.raises(ValidationError):
        CanonicalTelemetryEvent(
            device_id="DEV-0001",
            facility_id="FAC-01",
            timestamp="2026-10-30T10:15:30.123Z",
            temperature=50.0,
            vibration=-1.0,
            pressure=30.0,
            flow_rate=100.0,
            power_consumption=20.0,
            status_code=StatusCode.OK,
            location="Zone-A",
        )


def test_forbid_extra_fields():
    """Verify that unexpected extra attributes fail validation."""
    with pytest.raises(ValidationError):
        CanonicalTelemetryEvent(
            device_id="DEV-0001",
            facility_id="FAC-01",
            timestamp="2026-10-30T10:15:30.123Z",
            temperature=50.0,
            vibration=1.0,
            pressure=30.0,
            flow_rate=100.0,
            power_consumption=20.0,
            status_code=StatusCode.OK,
            location="Zone-A",
            unexpected_field="BAD_DATA",
        )

