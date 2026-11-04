"""Unit tests for Spark streaming schema definitions."""

import pytest

pyspark = pytest.importorskip("pyspark", reason="PySpark is only installed in the Spark container runtime")
if not hasattr(pyspark, "__file__") or "Mock" in type(pyspark).__name__:
    pytest.skip("PySpark is mocked on host environment; run schema tests inside Spark container", allow_module_level=True)

from streaming.schema import CANONICAL_SPARK_SCHEMA, STRING_MIRROR_SPARK_SCHEMA
from streaming.sinks.postgres import CANONICAL_TO_DDL_MAPPING


def test_schema_field_presence():
    """Verify all 11 canonical fields are present in CANONICAL_SPARK_SCHEMA."""
    field_names = set(CANONICAL_SPARK_SCHEMA.names)
    expected = {
        "event_id",
        "device_id",
        "facility_id",
        "timestamp",
        "temperature",
        "vibration",
        "pressure",
        "flow_rate",
        "power_consumption",
        "status_code",
        "location",
    }
    assert expected.issubset(field_names)


def test_string_mirror_schema_presence():
    """Verify all fields in string mirror schema are StringType."""
    for field in STRING_MIRROR_SPARK_SCHEMA.fields:
        assert field.dataType.typeName() == "string"


def test_canonical_to_ddl_mapping():
    """Verify single canonical to DDL mapping dictionary contains all necessary columns."""
    assert "event_id" in CANONICAL_TO_DDL_MAPPING
    assert "device_id" in CANONICAL_TO_DDL_MAPPING
    assert "facility_id" in CANONICAL_TO_DDL_MAPPING
    assert "temperature" in CANONICAL_TO_DDL_MAPPING
    assert "status_code" in CANONICAL_TO_DDL_MAPPING
