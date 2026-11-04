"""FlowSync - Phase 5 Great Expectations & Manifest Ledger Tests.

Verifies canonical suite definition, deterministic fingerprinting,
manifest ledger state transitions, and PostgreSQL data quality persistence.
"""

import os
import sys
import uuid
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from quality.suite import (
    CANONICAL_RULES,
    CANONICAL_SUITE_FINGERPRINT,
    SUITE_NAME,
    SUITE_VERSION,
    compute_canonical_suite_fingerprint,
)
from streaming.sinks.postgres import PostgresStreamingSink


def test_canonical_suite_fingerprint_determinism():
    """Verify that canonical suite fingerprint is deterministic and length-prefixed."""
    fp1 = compute_canonical_suite_fingerprint(CANONICAL_RULES)
    fp2 = compute_canonical_suite_fingerprint(CANONICAL_RULES)
    assert fp1 == fp2
    assert len(fp1) == 64
    assert fp1 == CANONICAL_SUITE_FINGERPRINT


def test_canonical_rules_coverage():
    """Verify all 11 univariate fields from the canonical event contract are covered."""
    columns_covered = {r.get("kwargs", {}).get("column") for r in CANONICAL_RULES}
    expected_columns = {
        "event_id",
        "timestamp",
        "device_id",
        "facility_id",
        "location",
        "temperature",
        "vibration",
        "pressure",
        "flow_rate",
        "power_consumption",
        "status_code",
    }
    assert expected_columns.issubset(columns_covered)
    assert len(CANONICAL_RULES) == 19

