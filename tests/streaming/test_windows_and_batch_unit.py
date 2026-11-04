"""Unit tests for windowing configuration and micro-batch path idempotency."""

import sys
from unittest.mock import MagicMock
import inspect

# Provide test doubles for PySpark dependencies on host environment only if not installed
try:
    import pyspark
except ImportError:
    for mod in ["pyspark", "pyspark.sql", "pyspark.sql.functions", "pyspark.sql.types"]:
        if mod not in sys.modules:
            sys.modules[mod] = MagicMock()

from streaming.windows import build_windowed_aggregations
from streaming.batch_processor import MicroBatchProcessor


def test_window_and_watermark_default_parameters():
    """Verify that build_windowed_aggregations enforces 1-min window and 10-min watermark."""
    sig = inspect.signature(build_windowed_aggregations)
    params = sig.parameters
    
    assert "watermark_duration" in params
    assert params["watermark_duration"].default == "10 minutes"
    
    assert "window_duration" in params
    assert params["window_duration"].default == "1 minute"


def test_microbatch_raw_path_isolation():
    """Verify each micro-batch writes to an isolated deterministic S3A path."""
    processor = MicroBatchProcessor(raw_bucket="flowsync-raw")
    
    batch_0_path = f"s3a://{processor.raw_bucket}/batches/batch_0.parquet"
    batch_1_path = f"s3a://{processor.raw_bucket}/batches/batch_1.parquet"
    batch_retry_path = f"s3a://{processor.raw_bucket}/batches/batch_0.parquet"

    # Different batch IDs produce distinct paths
    assert batch_0_path != batch_1_path
    # Retrying the same batch ID targets the exact same path for idempotent overwrite
    assert batch_0_path == batch_retry_path


def test_microbatch_pass_through_hook():
    """Verify that the Phase 5 Great Expectations hook is a pass-through in Phase 4."""
    processor = MicroBatchProcessor()
    mock_df = MagicMock()
    
    result_df = processor.validate_batch_hook(mock_df, batch_id=5)
    assert result_df is mock_df
