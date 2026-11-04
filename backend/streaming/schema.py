"""FlowSync - Spark Structured Streaming Schema Definitions.

Defines the PySpark StructType schemas for raw Kafka payloads, string mirrors,
and typed canonical telemetry dataframes.
"""

from pyspark.sql.types import (
    DoubleType,
    StringType,
    StructField,
    StructType,
    TimestampType,
)

# Canonical schema matching FlowSync CanonicalTelemetryEvent
CANONICAL_SPARK_SCHEMA = StructType([
    StructField("event_id", StringType(), False),
    StructField("device_id", StringType(), False),
    StructField("facility_id", StringType(), False),
    StructField("timestamp", StringType(), False),
    StructField("temperature", DoubleType(), False),
    StructField("vibration", DoubleType(), False),
    StructField("pressure", DoubleType(), False),
    StructField("flow_rate", DoubleType(), True),
    StructField("power_consumption", DoubleType(), True),
    StructField("status_code", StringType(), False),
    StructField("location", StringType(), False),
])

# String-mirror schema used for robust preliminary parsing to prevent
# Spark's silent dropping/nulling of type errors during from_json
STRING_MIRROR_SPARK_SCHEMA = StructType([
    StructField("event_id", StringType(), True),
    StructField("device_id", StringType(), True),
    StructField("facility_id", StringType(), True),
    StructField("timestamp", StringType(), True),
    StructField("temperature", StringType(), True),
    StructField("vibration", StringType(), True),
    StructField("pressure", StringType(), True),
    StructField("flow_rate", StringType(), True),
    StructField("power_consumption", StringType(), True),
    StructField("status_code", StringType(), True),
    StructField("location", StringType(), True),
])

