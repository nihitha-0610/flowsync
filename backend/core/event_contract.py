"""FlowSync - Canonical Event Contract & Schema Definitions.

Defines the Pydantic v2 canonical event contract, field validation rules,
physical sensor ranges, and JSON serialization helpers.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional, Tuple
from uuid import UUID, uuid4

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)

# Physical Sensor Boundaries & Valid Domains
PHYSICAL_RANGES: Dict[str, Tuple[float, float]] = {
    "temperature": (-40.0, 125.0),       # Celsius
    "vibration": (0.0, 15.0),             # mm/s
    "pressure": (0.0, 100.0),             # bar
    "flow_rate": (0.0, 500.0),            # L/min
    "power_consumption": (0.0, 100.0),    # kW
}

DEVICE_ID_REGEX = re.compile(r"^DEV-[0-9]{4}$")
FACILITY_ID_REGEX = re.compile(r"^FAC-[0-9]{2}$")


class StatusCode(str, Enum):
    """Permitted device operational status codes."""
    OK = "OK"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"
    MAINTENANCE = "MAINTENANCE"


class CanonicalTelemetryEvent(BaseModel):
    """Canonical event model for industrial IoT telemetry records.
    
    Guarantees structural, grammatical, and domain validity according to
    the FlowSync canonical data contract.
    """
    model_config = ConfigDict(
        populate_by_name=True,
        validate_assignment=True,
        extra="forbid",
        str_strip_whitespace=True,
    )

    event_id: str = Field(
        default_factory=lambda: str(uuid4()),
        description="Unique event identifier (UUID v4 or deterministic v5)",
    )
    device_id: str = Field(
        ...,
        description="Device identifier conforming to pattern DEV-XXXX",
    )
    facility_id: str = Field(
        ...,
        description="Facility identifier conforming to pattern FAC-XX",
    )
    timestamp: str = Field(
        ...,
        description="Event generation timestamp in ISO-8601 UTC with trailing 'Z'",
    )
    temperature: float = Field(
        ...,
        ge=PHYSICAL_RANGES["temperature"][0],
        le=PHYSICAL_RANGES["temperature"][1],
        description="Ambient/operational temperature in Celsius (-40.0 to 125.0)",
    )
    vibration: float = Field(
        ...,
        ge=PHYSICAL_RANGES["vibration"][0],
        le=PHYSICAL_RANGES["vibration"][1],
        description="Vibration amplitude in mm/s (0.0 to 15.0)",
    )
    pressure: float = Field(
        ...,
        ge=PHYSICAL_RANGES["pressure"][0],
        le=PHYSICAL_RANGES["pressure"][1],
        description="Hydraulic/pneumatic pressure in bar (0.0 to 100.0)",
    )
    flow_rate: float = Field(
        ...,
        ge=PHYSICAL_RANGES["flow_rate"][0],
        le=PHYSICAL_RANGES["flow_rate"][1],
        description="Fluid flow rate in L/min (0.0 to 500.0)",
    )
    power_consumption: float = Field(
        ...,
        ge=PHYSICAL_RANGES["power_consumption"][0],
        le=PHYSICAL_RANGES["power_consumption"][1],
        description="Electrical power consumption in kW (0.0 to 100.0)",
    )
    status_code: StatusCode = Field(
        ...,
        description="Device operating health status (OK, WARNING, CRITICAL, MAINTENANCE)",
    )
    location: str = Field(
        ...,
        min_length=2,
        max_length=64,
        description="Physical location or zone within the facility (e.g. Zone-A, Line-2)",
    )

    @field_validator("event_id")
    @classmethod
    def validate_uuid(cls, v: str) -> str:
        try:
            UUID(v)
            return v
        except (ValueError, AttributeError, TypeError):
            raise ValueError(f"Invalid event_id UUID format: {v}")

    @field_validator("device_id")
    @classmethod
    def validate_device_id(cls, v: str) -> str:
        if not DEVICE_ID_REGEX.match(v):
            raise ValueError(f"device_id '{v}' does not match pattern DEV-[0-9]{{4}}")
        return v

    @field_validator("facility_id")
    @classmethod
    def validate_facility_id(cls, v: str) -> str:
        if not FACILITY_ID_REGEX.match(v):
            raise ValueError(f"facility_id '{v}' does not match pattern FAC-[0-9]{{2}}")
        return v

    @field_validator("timestamp")
    @classmethod
    def validate_iso_timestamp(cls, v: str) -> str:
        if not isinstance(v, str):
            raise ValueError("timestamp must be a string")
        if not v.endswith("Z"):
            raise ValueError(f"timestamp must be in UTC ending with 'Z', got: {v}")
        
        # Verify parseability with datetime
        clean_ts = v[:-1] + "+00:00"
        try:
            dt = datetime.fromisoformat(clean_ts)
            if dt.tzinfo != timezone.utc:
                raise ValueError("timestamp must be in UTC timezone")
        except ValueError as e:
            raise ValueError(f"Invalid ISO-8601 timestamp '{v}': {e}")
        return v

    def to_canonical_dict(self) -> Dict[str, Any]:
        """Convert to dictionary matching canonical field names and formatted types."""
        d = self.model_dump()
        d["status_code"] = self.status_code.value
        return d

    def to_json_str(self) -> str:
        """Serialize to compact JSON string."""
        return self.model_dump_json()

    @classmethod
    def parse_raw_safe(cls, payload: str | bytes) -> Tuple[Optional[CanonicalTelemetryEvent], Optional[str]]:
        """Safely parse a JSON string or bytes into a CanonicalTelemetryEvent.
        
        Returns:
            Tuple of (event, None) on success, or (None, error_message) on failure.
        """
        try:
            if isinstance(payload, bytes):
                payload = payload.decode("utf-8")
            event = cls.model_validate_json(payload)
            return event, None
        except Exception as exc:
            return None, str(exc)

