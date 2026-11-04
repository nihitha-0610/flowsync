"""FlowSync - Stream Parsing, Type Casting & Structural Defect Isolation.

Performs robust string-mirror deserialization, strict type casting, regex enforcement,
domain bounds validation, and splits records into valid and quarantined dataframes.
"""

from __future__ import annotations

from pyspark.sql import DataFrame
from pyspark.sql.functions import (
    col,
    concat_ws,
    from_json,
    lit,
    to_timestamp,
    when,
)

from streaming.schema import STRING_MIRROR_SPARK_SCHEMA


def parse_and_validate_telemetry_stream(kafka_df: DataFrame) -> tuple[DataFrame, DataFrame]:
    """Pure transformation splitting raw Kafka records into valid_df and structural_reject_df.
    
    Args:
        kafka_df: Raw Kafka streaming DataFrame with (key, value, topic, partition, offset, timestamp)
        
    Returns:
        Tuple of (valid_df, structural_reject_df)
    """
    # 1. Cast key and value to string
    raw_df = kafka_df.select(
        col("topic").alias("kafka_topic"),
        col("partition").alias("kafka_partition"),
        col("offset").alias("kafka_offset"),
        col("timestamp").alias("kafka_timestamp"),
        col("key").cast("string").alias("kafka_key"),
        col("value").cast("string").alias("raw_payload"),
    )

    # 2. String-mirror JSON parsing to detect syntax malformations
    parsed_df = raw_df.withColumn(
        "json_parsed",
        from_json(col("raw_payload"), STRING_MIRROR_SPARK_SCHEMA)
    )

    # 3. Perform typed casting on extracted string fields
    typed_df = parsed_df.select(
        col("kafka_topic"),
        col("kafka_partition"),
        col("kafka_offset"),
        col("raw_payload"),
        col("json_parsed"),
        col("json_parsed.event_id").alias("raw_event_id"),
        col("json_parsed.device_id").alias("raw_device_id"),
        col("json_parsed.facility_id").alias("raw_facility_id"),
        col("json_parsed.timestamp").alias("raw_timestamp"),
        col("json_parsed.temperature").cast("double").alias("typed_temp"),
        col("json_parsed.vibration").cast("double").alias("typed_vibe"),
        col("json_parsed.pressure").cast("double").alias("typed_press"),
        col("json_parsed.flow_rate").cast("double").alias("typed_flow"),
        col("json_parsed.power_consumption").cast("double").alias("typed_power"),
        col("json_parsed.status_code").alias("raw_status"),
        col("json_parsed.location").alias("raw_location"),
    )

    # 4. Convert ISO-8601 UTC timestamp ending in 'Z' to Spark TimestampType
    timestamp_df = typed_df.withColumn(
        "typed_timestamp",
        to_timestamp(col("raw_timestamp"))
    )

    # 5. Defect condition checks
    cond_unparseable_json = col("json_parsed").isNull()

    cond_missing_required = (
        col("raw_event_id").isNull()
        | col("raw_device_id").isNull()
        | col("raw_facility_id").isNull()
        | col("raw_timestamp").isNull()
        | col("typed_temp").isNull()
        | col("typed_vibe").isNull()
        | col("typed_press").isNull()
        | col("raw_status").isNull()
        | col("raw_location").isNull()
    )

    cond_type_cast_failed = (
        (col("json_parsed.temperature").isNotNull() & col("typed_temp").isNull())
        | (col("json_parsed.vibration").isNotNull() & col("typed_vibe").isNull())
        | (col("json_parsed.pressure").isNotNull() & col("typed_press").isNull())
        | (col("json_parsed.flow_rate").isNotNull() & col("typed_flow").isNull())
        | (col("json_parsed.power_consumption").isNotNull() & col("typed_power").isNull())
    )

    cond_bad_device_id = ~col("raw_device_id").rlike(r"^DEV-[0-9]{4}$")
    cond_bad_facility_id = ~col("raw_facility_id").rlike(r"^FAC-[0-9]{2}$")
    cond_bad_status = ~col("raw_status").isin("OK", "WARNING", "CRITICAL", "MAINTENANCE")
    cond_bad_timestamp = col("typed_timestamp").isNull()

    cond_out_of_bounds = (
        (col("typed_temp") < -40.0) | (col("typed_temp") > 125.0)
        | (col("typed_vibe") < 0.0) | (col("typed_vibe") > 15.0)
        | (col("typed_press") < 0.0) | (col("typed_press") > 100.0)
        | (col("typed_flow") < 0.0) | (col("typed_flow") > 500.0)
        | (col("typed_power") < 0.0) | (col("typed_power") > 100.0)
    )

    # 6. Assign failure classification
    evaluated_df = timestamp_df.withColumn(
        "is_structural_reject",
        cond_unparseable_json
        | cond_missing_required
        | cond_type_cast_failed
        | cond_bad_device_id
        | cond_bad_facility_id
        | cond_bad_status
        | cond_bad_timestamp
        | cond_out_of_bounds
    ).withColumn(
        "failure_reason",
        when(cond_unparseable_json, lit("unparseable_json_syntax"))
        .when(cond_type_cast_failed, lit("numeric_type_cast_failure"))
        .when(cond_missing_required, lit("missing_mandatory_field"))
        .when(cond_bad_device_id, lit("invalid_device_id_format"))
        .when(cond_bad_facility_id, lit("invalid_facility_id_format"))
        .when(cond_bad_status, lit("invalid_status_code_enum"))
        .when(cond_bad_timestamp, lit("invalid_timestamp_format"))
        .when(cond_out_of_bounds, lit("physical_sensor_bounds_violation"))
        .otherwise(lit(None))
    ).withColumn(
        "failed_field",
        when(cond_unparseable_json, lit("payload"))
        .when(col("raw_device_id").isNull() | cond_bad_device_id, lit("device_id"))
        .when(col("raw_facility_id").isNull() | cond_bad_facility_id, lit("facility_id"))
        .when(col("raw_status").isNull() | cond_bad_status, lit("status_code"))
        .when(col("raw_timestamp").isNull() | cond_bad_timestamp, lit("timestamp"))
        .when(col("typed_temp").isNull() | (col("typed_temp") < -40.0) | (col("typed_temp") > 125.0), lit("temperature"))
        .when(col("typed_vibe").isNull() | (col("typed_vibe") < 0.0) | (col("typed_vibe") > 15.0), lit("vibration"))
        .when(col("typed_press").isNull() | (col("typed_press") < 0.0) | (col("typed_press") > 100.0), lit("pressure"))
        .otherwise(lit(None))
    )

    # 7. Split valid records
    valid_df = evaluated_df.filter(~col("is_structural_reject")).select(
        col("raw_event_id").alias("event_id"),
        col("raw_device_id").alias("device_id"),
        col("raw_facility_id").alias("facility_id"),
        col("raw_location").alias("location"),
        col("typed_timestamp").alias("timestamp"),
        col("typed_temp").alias("temperature"),
        col("typed_vibe").alias("vibration"),
        col("typed_press").alias("pressure"),
        col("typed_flow").alias("flow_rate"),
        col("typed_power").alias("power_consumption"),
        col("raw_status").alias("status_code"),
        col("kafka_topic"),
        col("kafka_partition"),
        col("kafka_offset"),
    )

    # 8. Split structural rejects
    structural_reject_df = evaluated_df.filter(col("is_structural_reject")).select(
        col("raw_event_id").alias("event_id"),
        col("typed_timestamp").alias("timestamp"),
        col("raw_payload"),
        col("kafka_topic"),
        col("kafka_partition"),
        col("kafka_offset"),
        lit("stream_parsing").alias("failure_stage"),
        col("failure_reason"),
        col("failed_field"),
        col("raw_payload").alias("observed_value"),
    )

    return valid_df, structural_reject_df

