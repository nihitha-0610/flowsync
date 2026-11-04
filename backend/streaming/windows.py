"""FlowSync - Tumbling Window Aggregations & Operational Metrics Pipeline.

Computes 1-minute event-time tumbling windows with watermarking for device telemetry,
calculating event counts, average/max temperatures, vibration, and pressure.
"""

from __future__ import annotations

import logging
from typing import Optional

from pyspark.sql import DataFrame
from pyspark.sql.functions import (
    avg,
    col,
    count,
    lit,
    max as spark_max,
    round as spark_round,
    window,
)

from streaming.sinks.postgres import PostgresStreamingSink

logger = logging.getLogger("flowsync.streaming.windows")


def build_windowed_aggregations(
    valid_df: DataFrame,
    watermark_duration: str = "10 minutes",
    window_duration: str = "1 minute",
) -> DataFrame:
    """Apply event-time watermarking and 1-minute tumbling window aggregations.
    
    Args:
        valid_df: DataFrame of valid telemetry events with typed 'timestamp' column
        watermark_duration: Watermark lateness threshold (e.g. '2 minutes')
        window_duration: Tumbling window size (e.g. '1 minute')
        
    Returns:
        Aggregated streaming DataFrame
    """
    watermarked_df = valid_df.withWatermark("timestamp", watermark_duration)

    aggregated_df = (
        watermarked_df.groupBy(
            window(col("timestamp"), window_duration),
            col("device_id"),
        )
        .agg(
            count(lit("*")).alias("event_count"),
            spark_round(avg("temperature"), 2).alias("avg_temperature"),
            spark_round(spark_max("temperature"), 2).alias("max_temperature"),
            spark_round(avg("vibration"), 3).alias("avg_vibration"),
            spark_round(spark_max("vibration"), 3).alias("max_vibration"),
            spark_round(avg("pressure"), 2).alias("avg_pressure"),
        )
        .select(
            col("window.start").alias("window_start"),
            col("window.end").alias("window_end"),
            col("device_id"),
            col("event_count"),
            col("avg_temperature"),
            col("max_temperature"),
            col("avg_vibration"),
            col("max_vibration"),
            col("avg_pressure"),
        )
    )

    return aggregated_df


class WindowedMetricsProcessor:
    """foreachBatch handler for persisting windowed metrics to PostgreSQL."""

    def __init__(self, postgres_sink: Optional[PostgresStreamingSink] = None):
        self.postgres_sink = postgres_sink or PostgresStreamingSink()

    def process_windowed_batch(self, batch_df: DataFrame, batch_id: int):
        """Persist aggregated windowed metrics to pipeline_windowed_metrics."""
        count_rows = batch_df.count()
        if count_rows == 0:
            return

        logger.info("Persisting %d windowed metric rows for batch %d", count_rows, batch_id)
        records = [row.asDict() for row in batch_df.collect()]
        self.postgres_sink.write_windowed_metrics(records)
