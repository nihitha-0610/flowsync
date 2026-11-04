"""FlowSync - Streaming Query Metrics Exporter & Prometheus Instrumentation.

Exposes real-time throughput, batch duration, and record counters to Prometheus
on dedicated HTTP server (default port 8000).
"""

from __future__ import annotations

import logging
import threading
import time
from typing import Any, Dict

from prometheus_client import (
    Counter,
    Gauge,
    Histogram,
    start_http_server,
)

logger = logging.getLogger("flowsync.streaming.metrics")

# Prometheus Metric Collectors
STREAM_INPUT_ROWS = Counter(
    "flowsync_stream_input_rows_total",
    "Cumulative total input telemetry records consumed by Spark",
    ["query_name"],
)

STREAM_PROCESSED_ROWS = Counter(
    "flowsync_stream_processed_rows_total",
    "Cumulative total valid telemetry records successfully processed",
    ["query_name"],
)

STREAM_REJECTED_ROWS = Counter(
    "flowsync_stream_rejected_rows_total",
    "Cumulative total structural defect records quarantined",
    ["query_name"],
)

STREAM_BATCH_DURATION = Histogram(
    "flowsync_stream_batch_duration_seconds",
    "Execution duration of micro-batches in seconds",
    ["query_name"],
    buckets=(0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
)

STREAM_INPUT_RATE = Gauge(
    "flowsync_stream_input_rate_eps",
    "Instantaneous input rate in events per second",
    ["query_name"],
)

STREAM_PROCESSING_RATE = Gauge(
    "flowsync_stream_processing_rate_eps",
    "Instantaneous processing rate in events per second",
    ["query_name"],
)

STREAM_ACTIVE_QUERIES = Gauge(
    "flowsync_stream_active_queries",
    "Number of actively running streaming queries",
)


def start_streaming_metrics_server(port: int = 8000):
    """Start the background HTTP server exposing Prometheus metrics."""
    try:
        start_http_server(port)
        logger.info("Spark streaming Prometheus metrics server started on port %d", port)
    except Exception as exc:
        logger.warning("Could not bind Prometheus metrics server on port %d: %s", port, exc)


def update_streaming_metrics(
    query_name: str,
    input_rows: int,
    processed_rows: int,
    rejected_rows: int,
    duration_seconds: float,
    input_rate: float = 0.0,
    processing_rate: float = 0.0,
    is_retry: bool = False,
):
    """Update Prometheus metrics with micro-batch execution statistics.

    Args:
        query_name: Name of the streaming query
        input_rows: Total raw records in micro-batch
        processed_rows: Valid records processed and persisted
        rejected_rows: Structural defect records quarantined
        duration_seconds: Processing elapsed time in seconds
        input_rate: Raw records consumed per second
        processing_rate: Valid records processed per second
        is_retry: Whether this batch execution is a retry/replay of an already committed batch
    """
    if not is_retry:
        STREAM_INPUT_ROWS.labels(query_name=query_name).inc(input_rows)
        STREAM_PROCESSED_ROWS.labels(query_name=query_name).inc(processed_rows)
        STREAM_REJECTED_ROWS.labels(query_name=query_name).inc(rejected_rows)
    STREAM_BATCH_DURATION.labels(query_name=query_name).observe(max(duration_seconds, 0.0))
    STREAM_INPUT_RATE.labels(query_name=query_name).set(max(input_rate, 0.0))
    STREAM_PROCESSING_RATE.labels(query_name=query_name).set(max(processing_rate, 0.0))
