"""FlowSync - Great Expectations Canonical Suite & Deterministic Registry.

Defines the Great Expectations 1.24.1 ExpectationSuite mirroring the 11 univariate
fields of the canonical event contract, and provides length-prefixed SHA-256 fingerprinting.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, List, Tuple

try:
    import great_expectations as gx
    import great_expectations.expectations as gxe
    from great_expectations.core.expectation_suite import ExpectationSuite
except ImportError:
    gx = Any  # type: ignore
    gxe = Any  # type: ignore
    ExpectationSuite = Any  # type: ignore

SUITE_NAME = "flowsync_canonical_suite"
SUITE_VERSION = "1.0.0"

# Canonical univariate rules matching backend/core/event_contract.py
CANONICAL_RULES: List[Dict[str, Any]] = [
    {"type": "expect_column_values_to_not_be_null", "kwargs": {"column": "event_id"}},
    {
        "type": "expect_column_values_to_match_regex",
        "kwargs": {
            "column": "event_id",
            "regex": r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
        },
    },
    {"type": "expect_column_values_to_not_be_null", "kwargs": {"column": "timestamp"}},
    {"type": "expect_column_values_to_not_be_null", "kwargs": {"column": "device_id"}},
    {
        "type": "expect_column_values_to_match_regex",
        "kwargs": {"column": "device_id", "regex": r"^DEV-[0-9]{4}$"},
    },
    {"type": "expect_column_values_to_not_be_null", "kwargs": {"column": "facility_id"}},
    {
        "type": "expect_column_values_to_match_regex",
        "kwargs": {"column": "facility_id", "regex": r"^FAC-[0-9]{2}$"},
    },
    {"type": "expect_column_values_to_not_be_null", "kwargs": {"column": "location"}},
    {
        "type": "expect_column_value_lengths_to_be_between",
        "kwargs": {"column": "location", "min_value": 2, "max_value": 64},
    },
    {"type": "expect_column_values_to_not_be_null", "kwargs": {"column": "temperature"}},
    {
        "type": "expect_column_values_to_be_between",
        "kwargs": {"column": "temperature", "min_value": -40.0, "max_value": 125.0},
    },
    {"type": "expect_column_values_to_not_be_null", "kwargs": {"column": "vibration"}},
    {
        "type": "expect_column_values_to_be_between",
        "kwargs": {"column": "vibration", "min_value": 0.0, "max_value": 15.0},
    },
    {"type": "expect_column_values_to_not_be_null", "kwargs": {"column": "pressure"}},
    {
        "type": "expect_column_values_to_be_between",
        "kwargs": {"column": "pressure", "min_value": 0.0, "max_value": 100.0},
    },
    {
        "type": "expect_column_values_to_be_between",
        "kwargs": {"column": "flow_rate", "min_value": 0.0, "max_value": 500.0},
    },
    {
        "type": "expect_column_values_to_be_between",
        "kwargs": {"column": "power_consumption", "min_value": 0.0, "max_value": 100.0},
    },
    {"type": "expect_column_values_to_not_be_null", "kwargs": {"column": "status_code"}},
    {
        "type": "expect_column_values_to_be_in_set",
        "kwargs": {
            "column": "status_code",
            "value_set": ["OK", "WARNING", "CRITICAL", "MAINTENANCE"],
        },
    },
]


def compute_canonical_suite_fingerprint(rules: List[Dict[str, Any]]) -> str:
    """Compute length-prefixed SHA-256 fingerprint over semantic expectation rules."""
    hasher = hashlib.sha256()
    # Sort rules deterministically by type and column
    sorted_rules = sorted(
        rules,
        key=lambda r: (r.get("type", ""), r.get("kwargs", {}).get("column", "")),
    )
    for r in sorted_rules:
        rule_str = json.dumps(r, sort_keys=True)
        rule_bytes = rule_str.encode("utf-8")
        hasher.update(f"{len(rule_bytes)}:".encode("utf-8") + rule_bytes)
    return hasher.hexdigest()


CANONICAL_SUITE_FINGERPRINT = compute_canonical_suite_fingerprint(CANONICAL_RULES)


def build_canonical_expectation_suite(context: Any = None, suite_name: str = SUITE_NAME) -> ExpectationSuite:
    """Instantiate a Great Expectations 1.24.1 ExpectationSuite with canonical contract rules."""
    if context is None:
        context = gx.get_context(mode="ephemeral")
    suite = ExpectationSuite(name=suite_name)
    context.suites.add(suite)
    
    # 1. event_id
    suite.add_expectation(gxe.ExpectColumnValuesToNotBeNull(column="event_id"))
    suite.add_expectation(
        gxe.ExpectColumnValuesToMatchRegex(
            column="event_id",
            regex=r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
        )
    )
    # 2. timestamp
    suite.add_expectation(gxe.ExpectColumnValuesToNotBeNull(column="timestamp"))
    # 3. device_id
    suite.add_expectation(gxe.ExpectColumnValuesToNotBeNull(column="device_id"))
    suite.add_expectation(
        gxe.ExpectColumnValuesToMatchRegex(column="device_id", regex=r"^DEV-[0-9]{4}$")
    )
    # 4. facility_id
    suite.add_expectation(gxe.ExpectColumnValuesToNotBeNull(column="facility_id"))
    suite.add_expectation(
        gxe.ExpectColumnValuesToMatchRegex(column="facility_id", regex=r"^FAC-[0-9]{2}$")
    )
    # 5. location
    suite.add_expectation(gxe.ExpectColumnValuesToNotBeNull(column="location"))
    suite.add_expectation(
        gxe.ExpectColumnValueLengthsToBeBetween(column="location", min_value=2, max_value=64)
    )
    # 6. temperature
    suite.add_expectation(gxe.ExpectColumnValuesToNotBeNull(column="temperature"))
    suite.add_expectation(
        gxe.ExpectColumnValuesToBeBetween(column="temperature", min_value=-40.0, max_value=125.0)
    )
    # 7. vibration
    suite.add_expectation(gxe.ExpectColumnValuesToNotBeNull(column="vibration"))
    suite.add_expectation(
        gxe.ExpectColumnValuesToBeBetween(column="vibration", min_value=0.0, max_value=15.0)
    )
    # 8. pressure
    suite.add_expectation(gxe.ExpectColumnValuesToNotBeNull(column="pressure"))
    suite.add_expectation(
        gxe.ExpectColumnValuesToBeBetween(column="pressure", min_value=0.0, max_value=100.0)
    )
    # 9. flow_rate
    suite.add_expectation(
        gxe.ExpectColumnValuesToBeBetween(column="flow_rate", min_value=0.0, max_value=500.0)
    )
    # 10. power_consumption
    suite.add_expectation(
        gxe.ExpectColumnValuesToBeBetween(
            column="power_consumption", min_value=0.0, max_value=100.0
        )
    )
    # 11. status_code
    suite.add_expectation(gxe.ExpectColumnValuesToNotBeNull(column="status_code"))
    suite.add_expectation(
        gxe.ExpectColumnValuesToBeInSet(
            column="status_code",
            value_set=["OK", "WARNING", "CRITICAL", "MAINTENANCE"],
        )
    )
    return suite
