"""Unit tests for PostgreSQL streaming sink and DDL mapping."""

from unittest.mock import MagicMock
import pytest

from streaming.sinks.postgres import PostgresStreamingSink, CANONICAL_TO_DDL_MAPPING


@pytest.fixture
def mock_postgres_sink():
    sink = PostgresStreamingSink()
    sink.get_connection = MagicMock()
    return sink


def test_write_valid_events_idempotent_sql(mock_postgres_sink):
    """Verify executemany called with ON CONFLICT DO NOTHING query."""
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_conn.__enter__.return_value = mock_conn
    mock_cur.__enter__.return_value = mock_cur
    mock_conn.cursor.return_value = mock_cur
    mock_postgres_sink.get_connection.return_value = mock_conn

    rows = [
        {
            "event_id": "11111111-1111-1111-1111-111111111111",
            "timestamp": "2026-10-30T10:00:00Z",
            "device_id": "DEV-0001",
            "facility_id": "FAC-01",
            "location": "Zone-A",
            "temperature": 50.0,
            "vibration": 1.5,
            "pressure": 35.0,
            "flow_rate": 120.0,
            "power_consumption": 25.0,
            "status_code": "OK",
        }
    ]

    count = mock_postgres_sink.write_valid_events(rows)
    assert count == 1
    assert mock_cur.executemany.called
    sql_arg = mock_cur.executemany.call_args[0][0]
    assert "ON CONFLICT (event_id) DO NOTHING" in sql_arg
    assert mock_conn.commit.called


def test_write_invalid_events_quarantine_sql(mock_postgres_sink):
    """Verify quarantine records persisted with failure reason and coordinates."""
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_conn.__enter__.return_value = mock_conn
    mock_cur.__enter__.return_value = mock_cur
    mock_conn.cursor.return_value = mock_cur
    mock_postgres_sink.get_connection.return_value = mock_conn

    reject_rows = [
        {
            "event_id": None,
            "timestamp": None,
            "raw_payload": "{bad_json",
            "raw_text": "{bad_json",
            "kafka_topic": "events.raw",
            "kafka_partition": 0,
            "kafka_offset": 12345,
            "failure_stage": "stream_parsing",
            "failure_reason": "unparseable_json_syntax",
            "failed_field": "payload",
            "observed_value": "{bad_json",
            "violations": None,
        }
    ]

    count = mock_postgres_sink.write_invalid_events(reject_rows)
    assert count == 1
    assert mock_cur.executemany.called
    sql_arg = mock_cur.executemany.call_args[0][0]
    assert "ON CONFLICT (kafka_topic, kafka_partition, kafka_offset)" in sql_arg
    assert mock_conn.commit.called

