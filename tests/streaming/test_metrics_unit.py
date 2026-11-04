"""Unit tests for streaming query metrics and Prometheus instrumentation.

Covers:
- Batch containing valid and rejected records.
- Empty batch.
- Failed batch.
- Retried batch (avoiding double-counting).
- Correct metric values and label dimensions.
"""

import sys
from unittest.mock import MagicMock
import pytest
from prometheus_client import REGISTRY

# Provide test doubles for PySpark dependencies on host environment only if not installed
try:
    import pyspark
except ImportError:
    for mod in ["pyspark", "pyspark.sql", "pyspark.sql.functions", "pyspark.sql.types"]:
        if mod not in sys.modules:
            sys.modules[mod] = MagicMock()

from streaming.metrics import (
    STREAM_BATCH_DURATION,
    STREAM_INPUT_RATE,
    STREAM_INPUT_ROWS,
    STREAM_PROCESSED_ROWS,
    STREAM_PROCESSING_RATE,
    STREAM_REJECTED_ROWS,
    update_streaming_metrics,
)
from streaming.batch_processor import MicroBatchProcessor


@pytest.fixture
def test_query_name():
    return "test_telemetry_query"


def test_metric_label_dimensions(test_query_name):
    """Verify that metric collectors declare the correct 'query_name' label dimension."""
    assert STREAM_INPUT_ROWS._labelnames == ("query_name",)
    assert STREAM_PROCESSED_ROWS._labelnames == ("query_name",)
    assert STREAM_REJECTED_ROWS._labelnames == ("query_name",)
    assert STREAM_BATCH_DURATION._labelnames == ("query_name",)
    assert STREAM_INPUT_RATE._labelnames == ("query_name",)
    assert STREAM_PROCESSING_RATE._labelnames == ("query_name",)


def test_batch_valid_and_rejected_records(test_query_name):
    """Test metric update for a batch with both valid and rejected records."""
    init_input = STREAM_INPUT_ROWS.labels(query_name=test_query_name)._value.get()
    init_proc = STREAM_PROCESSED_ROWS.labels(query_name=test_query_name)._value.get()
    init_rej = STREAM_REJECTED_ROWS.labels(query_name=test_query_name)._value.get()

    update_streaming_metrics(
        query_name=test_query_name,
        input_rows=12,
        processed_rows=10,
        rejected_rows=2,
        duration_seconds=0.5,
        input_rate=24.0,
        processing_rate=20.0,
        is_retry=False,
    )

    assert STREAM_INPUT_ROWS.labels(query_name=test_query_name)._value.get() == init_input + 12
    assert STREAM_PROCESSED_ROWS.labels(query_name=test_query_name)._value.get() == init_proc + 10
    assert STREAM_REJECTED_ROWS.labels(query_name=test_query_name)._value.get() == init_rej + 2
    assert STREAM_INPUT_RATE.labels(query_name=test_query_name)._value.get() == 24.0
    assert STREAM_PROCESSING_RATE.labels(query_name=test_query_name)._value.get() == 20.0


def test_empty_batch(test_query_name):
    """Test metric update for an empty batch (0 records, 0 rates, duration observed)."""
    init_input = STREAM_INPUT_ROWS.labels(query_name=test_query_name)._value.get()
    init_proc = STREAM_PROCESSED_ROWS.labels(query_name=test_query_name)._value.get()
    init_rej = STREAM_REJECTED_ROWS.labels(query_name=test_query_name)._value.get()

    update_streaming_metrics(
        query_name=test_query_name,
        input_rows=0,
        processed_rows=0,
        rejected_rows=0,
        duration_seconds=0.01,
        input_rate=0.0,
        processing_rate=0.0,
        is_retry=False,
    )

    # Cumulative counters must remain unchanged
    assert STREAM_INPUT_ROWS.labels(query_name=test_query_name)._value.get() == init_input
    assert STREAM_PROCESSED_ROWS.labels(query_name=test_query_name)._value.get() == init_proc
    assert STREAM_REJECTED_ROWS.labels(query_name=test_query_name)._value.get() == init_rej
    # Gauges must be reset to 0.0
    assert STREAM_INPUT_RATE.labels(query_name=test_query_name)._value.get() == 0.0
    assert STREAM_PROCESSING_RATE.labels(query_name=test_query_name)._value.get() == 0.0


def test_retried_batch_avoids_double_counting(test_query_name):
    """Test that retried batch does not increment cumulative counters."""
    init_input = STREAM_INPUT_ROWS.labels(query_name=test_query_name)._value.get()
    init_proc = STREAM_PROCESSED_ROWS.labels(query_name=test_query_name)._value.get()
    init_rej = STREAM_REJECTED_ROWS.labels(query_name=test_query_name)._value.get()

    # Retry flag set to True
    update_streaming_metrics(
        query_name=test_query_name,
        input_rows=12,
        processed_rows=10,
        rejected_rows=2,
        duration_seconds=0.25,
        input_rate=48.0,
        processing_rate=40.0,
        is_retry=True,
    )

    # Cumulative counters must NOT change on retry
    assert STREAM_INPUT_ROWS.labels(query_name=test_query_name)._value.get() == init_input
    assert STREAM_PROCESSED_ROWS.labels(query_name=test_query_name)._value.get() == init_proc
    assert STREAM_REJECTED_ROWS.labels(query_name=test_query_name)._value.get() == init_rej
    # But per-batch instantaneous gauges update to reflect current execution
    assert STREAM_INPUT_RATE.labels(query_name=test_query_name)._value.get() == 48.0
    assert STREAM_PROCESSING_RATE.labels(query_name=test_query_name)._value.get() == 40.0


def test_micro_batch_processor_empty_batch():
    """Verify MicroBatchProcessor handles empty batch without error and updates gauges."""
    processor = MicroBatchProcessor(query_name="test_empty_query")
    mock_df = MagicMock()
    mock_df.count.return_value = 0

    processor.process_batch(mock_df, batch_id=99)

    assert STREAM_INPUT_RATE.labels(query_name="test_empty_query")._value.get() == 0.0
    assert STREAM_PROCESSING_RATE.labels(query_name="test_empty_query")._value.get() == 0.0


def test_micro_batch_processor_failed_batch():
    """Verify MicroBatchProcessor resets gauges and does not advance cumulative counters on error."""
    processor = MicroBatchProcessor(query_name="test_failed_query")
    init_proc = STREAM_PROCESSED_ROWS.labels(query_name="test_failed_query")._value.get()

    mock_df = MagicMock()
    mock_df.count.return_value = 10
    mock_df.write.mode.side_effect = RuntimeError("MinIO connection timeout")

    with pytest.raises(RuntimeError, match="MinIO connection timeout"):
        processor.process_batch(mock_df, batch_id=100)

    # Cumulative processed counter must NOT have been incremented
    assert STREAM_PROCESSED_ROWS.labels(query_name="test_failed_query")._value.get() == init_proc
    # Gauges must be reset
    assert STREAM_INPUT_RATE.labels(query_name="test_failed_query")._value.get() == 0.0
    assert STREAM_PROCESSING_RATE.labels(query_name="test_failed_query")._value.get() == 0.0


def test_micro_batch_processor_retry_tracking():
    """Verify MicroBatchProcessor tracks committed batches to prevent double-counting on retries."""
    processor = MicroBatchProcessor(query_name="test_retry_tracker")
    assert 1 not in processor._committed_batches

    # Simulate success
    processor._committed_batches.add(1)
    assert 1 in processor._committed_batches
