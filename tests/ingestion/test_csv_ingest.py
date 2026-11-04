"""Unit tests for FlowSync Streaming CSV Ingestion Engine."""

import os
import pytest
from unittest.mock import MagicMock

from ingestion.csv_ingest import CsvIngestionEngine
from ingestion.producer import KafkaEventProducer


@pytest.fixture
def mock_producer():
    producer = MagicMock(spec=KafkaEventProducer)
    producer.publish.return_value = True
    producer.publish_dlq.return_value = True
    producer.flush.return_value = 0
    return producer


def test_csv_ingest_valid_file(mock_producer):
    """Verify that sample_telemetry_valid.csv produces 100% valid records."""
    csv_path = os.path.join("data", "sample_telemetry_valid.csv")
    engine = CsvIngestionEngine(producer=mock_producer)
    result = engine.ingest_file(csv_path)

    assert result.total_rows == 50
    assert result.valid_rows == 50
    assert result.rejected_rows == 0
    assert mock_producer.publish.call_count == 50
    assert mock_producer.publish_dlq.call_count == 0


def test_csv_ingest_mixed_file(mock_producer):
    """Verify that sample_telemetry_mixed.csv separates valid rows from DLQ rejects."""
    csv_path = os.path.join("data", "sample_telemetry_mixed.csv")
    engine = CsvIngestionEngine(producer=mock_producer)
    result = engine.ingest_file(csv_path)

    # Note: 'duplicate' and 'late' corruptions have valid syntax so they pass
    # structural CSV validation (they are rejected downstream by deduplication and watermarking)
    assert result.total_rows == 50
    assert result.valid_rows == 42
    assert result.rejected_rows == 8
    assert mock_producer.publish.call_count == 42
    assert mock_producer.publish_dlq.call_count == 8
