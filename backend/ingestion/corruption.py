"""FlowSync - Synthetic Telemetry Corruption & Chaos Injector.

Provides deterministic and randomized injectors to generate invalid,
malformed, late, or corrupt payloads for testing pipeline resilience,
schema enforcement, dead letter queues, and quarantine workflows.
"""

from __future__ import annotations

import copy
import json
import random
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


class CorruptionKind(str, Enum):
    """Categorized types of data defect injection."""
    MISSING_FIELD = "missing_field"
    NULL_VALUE = "null_value"
    WRONG_TYPE = "wrong_type"
    OUT_OF_RANGE = "out_of_range"
    BAD_TIMESTAMP = "bad_timestamp"
    BAD_DEVICE_ID = "bad_device_id"
    BAD_STATUS = "bad_status"
    TRUNCATED_JSON = "truncated_json"
    DUPLICATE = "duplicate"
    LATE = "late"


class CorruptionInjector:
    """Injects intentional structural, semantic, or timing defects into telemetry payloads."""

    def __init__(self, seed: Optional[int] = None):
        self._rng = random.Random(seed)

    def inject(
        self,
        event_dict: Dict[str, Any],
        kind: Optional[CorruptionKind] = None,
    ) -> Tuple[Dict[str, Any] | str, CorruptionKind, str]:
        """Inject a specific or randomly selected defect into the event dictionary.
        
        Returns:
            Tuple of:
            - corrupted_payload: Dict or raw str (if truncated json)
            - kind_applied: CorruptionKind
            - reason: Explanation of the injected defect
        """
        payload = copy.deepcopy(event_dict)
        if kind is None:
            kind = self._rng.choice(list(CorruptionKind))

        if kind == CorruptionKind.MISSING_FIELD:
            target_field = self._rng.choice(["timestamp", "temperature", "device_id", "status_code", "pressure"])
            payload.pop(target_field, None)
            return payload, kind, f"Dropped required field '{target_field}'"

        elif kind == CorruptionKind.NULL_VALUE:
            target_field = self._rng.choice(["temperature", "vibration", "device_id", "facility_id"])
            payload[target_field] = None
            return payload, kind, f"Set field '{target_field}' to null"

        elif kind == CorruptionKind.WRONG_TYPE:
            target_field = self._rng.choice(["temperature", "pressure", "power_consumption"])
            payload[target_field] = "INVALID_FLOAT_STRING"
            return payload, kind, f"Replaced numeric field '{target_field}' with non-parseable string"

        elif kind == CorruptionKind.OUT_OF_RANGE:
            # Physical bounds violation
            target_field = self._rng.choice(["temperature", "vibration", "pressure"])
            if target_field == "temperature":
                payload[target_field] = 9999.0  # Physical max 125.0
            elif target_field == "vibration":
                payload[target_field] = -50.0   # Physical min 0.0
            else:
                payload[target_field] = 500.0   # Physical max 100.0
            return payload, kind, f"Set '{target_field}' to out-of-range value {payload[target_field]}"

        elif kind == CorruptionKind.BAD_TIMESTAMP:
            malformed_ts = self._rng.choice([
                "2026/10/30 14:00:00",      # Non-ISO format
                "2026-10-30T10:15:30",       # Missing trailing 'Z'
                "NOT_A_TIMESTAMP_STRING",   # Pure gibberish
            ])
            payload["timestamp"] = malformed_ts
            return payload, kind, f"Injected non-conforming timestamp '{malformed_ts}'"

        elif kind == CorruptionKind.BAD_DEVICE_ID:
            bad_id = self._rng.choice(["SENSOR_99", "DEV1234", "DEV-99", "DEVICE-0001"])
            payload["device_id"] = bad_id
            return payload, kind, f"Violated device_id regex with '{bad_id}'"

        elif kind == CorruptionKind.BAD_STATUS:
            bad_status = self._rng.choice(["DESTROYED", "UNKNOWN_ERR", "OFFLINE_UNSUPPORTED", "123"])
            payload["status_code"] = bad_status
            return payload, kind, f"Violated status_code enum with '{bad_status}'"

        elif kind == CorruptionKind.TRUNCATED_JSON:
            raw_json = json.dumps(payload)
            # Cut off the last 15-25 characters to break JSON syntax
            cut_idx = max(10, len(raw_json) - self._rng.randint(15, 30))
            truncated = raw_json[:cut_idx]
            return truncated, kind, "Prematurely severed JSON string payload"

        elif kind == CorruptionKind.DUPLICATE:
            # Reuses the exact event_id
            return payload, kind, f"Marked as duplicate payload with existing event_id {payload.get('event_id')}"

        elif kind == CorruptionKind.LATE:
            # Inject a timestamp 15 minutes in the past
            try:
                base_time = datetime.fromisoformat(payload["timestamp"].replace("Z", "+00:00"))
            except Exception:
                base_time = datetime.now(timezone.utc)
            late_time = base_time - timedelta(minutes=15)
            payload["timestamp"] = late_time.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
            return payload, kind, f"Backdated timestamp 15 minutes for watermark testing ({payload['timestamp']})"

        return payload, CorruptionKind.MISSING_FIELD, "Default fallback corruption"

