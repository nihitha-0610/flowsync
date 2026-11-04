"""Unit tests for KafkaEventProducer configuration, callbacks, and resiliency."""

from unittest.mock import MagicMock, patch
import pytest

from ingestion.producer import KafkaEventProducer


def test_producer_configuration_idempotence():
    """Verify producer is initialized with idempotence and strict acks."""
    with patch("ingestion.producer.Producer") as mock_producer_cls:
        producer = KafkaEventProducer(bootstrap_servers="localhost:9094")
        
        # Verify Producer was initialized with expected config
        mock_producer_cls.assert_called_once()
        conf = mock_producer_cls.call_args[0][0]
        assert conf["enable.idempotence"] is True
        assert conf["acks"] == "all"
        assert conf["bootstrap.servers"] == "localhost:9094"
        assert conf["compression.type"] == "snappy"


def test_producer_delivery_callback_success():
    """Verify successful delivery callback updates metrics."""
    with patch("ingestion.producer.Producer"):
        producer = KafkaEventProducer(bootstrap_servers="localhost:9094")
        assert producer.delivered_count == 0
        assert producer.failed_count == 0

        # Simulate confluent_kafka.Message success callback
        mock_msg = MagicMock()
        mock_msg.topic.return_value = "events.raw"
        mock_msg.partition.return_value = 0
        mock_msg.offset.return_value = 42

        producer._delivery_callback(None, mock_msg)
        assert producer.delivered_count == 1
        assert producer.failed_count == 0


def test_producer_delivery_callback_failure():
    """Verify failed delivery callback increments failed count and records error."""
    with patch("ingestion.producer.Producer"):
        producer = KafkaEventProducer(bootstrap_servers="localhost:9094")
        
        mock_err = MagicMock()
        mock_err.str.return_value = "Broker: Message timed out"
        mock_msg = MagicMock()
        mock_msg.topic.return_value = "events.raw"
        mock_msg.partition.return_value = 1

        producer._delivery_callback(mock_err, mock_msg)
        assert producer.failed_count == 1
        assert producer.delivered_count == 0
        assert producer._last_delivery_error == "Broker: Message timed out"


def test_producer_publish_sync_flush():
    """Verify synchronous publishing calls flush."""
    with patch("ingestion.producer.Producer") as mock_producer_cls:
        mock_inner_producer = mock_producer_cls.return_value
        producer = KafkaEventProducer(bootstrap_servers="localhost:9094")

        success = producer.publish("events.raw", {"device_id": "DEV-0001"}, sync=True)
        assert success is True
        mock_inner_producer.produce.assert_called_once()
        mock_inner_producer.flush.assert_called_once()

