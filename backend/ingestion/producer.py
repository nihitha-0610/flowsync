"""FlowSync - Resilient Idempotent Kafka Event Producer.

Wraps confluent_kafka.Producer with enterprise delivery guarantees,
idempotence, backpressure handling, metrics tracking, and DLQ fallback.
"""

from __future__ import annotations

import json
import logging
import time
from typing import Any, Callable, Dict, List, Optional, Tuple

import confluent_kafka
from confluent_kafka import KafkaError, KafkaException, Producer

from core.config import get_settings

logger = logging.getLogger("flowsync.ingestion.producer")


class KafkaEventProducer:
    """Production-grade idempotent Kafka producer with DLQ fallback."""

    def __init__(
        self,
        bootstrap_servers: Optional[str] = None,
        dlq_topic: Optional[str] = None,
        client_id: str = "flowsync-producer",
        extra_config: Optional[Dict[str, Any]] = None,
    ):
        settings = get_settings()
        self.bootstrap_servers = bootstrap_servers or settings.KAFKA_BROKER_EXTERNAL
        self.dlq_topic = dlq_topic or settings.KAFKA_TOPIC_DLQ
        self.client_id = client_id

        # Producer configuration with idempotence and durability
        conf: Dict[str, Any] = {
            "bootstrap.servers": self.bootstrap_servers,
            "client.id": self.client_id,
            "enable.idempotence": True,
            "acks": "all",
            "retries": 5,
            "retry.backoff.ms": 200,
            "queue.buffering.max.messages": 100000,
            "queue.buffering.max.kbytes": 65536,
            "linger.ms": 10,
            "batch.num.messages": 500,
            "compression.type": "snappy",
        }
        if extra_config:
            conf.update(extra_config)

        self._conf = conf
        self._producer = Producer(conf)

        # Performance & Delivery Metrics
        self.published_count = 0
        self.delivered_count = 0
        self.failed_count = 0
        self.dlq_count = 0
        self._last_delivery_error: Optional[str] = None

    def _delivery_callback(self, err: Optional[KafkaError], msg: confluent_kafka.Message):
        """Internal callback invoked on message delivery success or failure."""
        if err is not None:
            self.failed_count += 1
            self._last_delivery_error = err.str()
            logger.error(
                "Message delivery failed on topic %s [partition %s]: %s",
                msg.topic(),
                msg.partition(),
                err.str(),
            )
        else:
            self.delivered_count += 1
            logger.debug(
                "Message delivered to %s [%s] @ offset %s",
                msg.topic(),
                msg.partition(),
                msg.offset(),
            )

    def publish(
        self,
        topic: str,
        value: str | bytes | Dict[str, Any],
        key: Optional[str] = None,
        headers: Optional[Dict[str, str] | List[Tuple[str, bytes]]] = None,
        sync: bool = False,
    ) -> bool:
        """Publish a message to the specified Kafka topic.
        
        Handles string/dict serialization, buffer backpressure, and optional sync wait.
        """
        # Serialize payload if dict
        if isinstance(value, dict):
            serialized_val = json.dumps(value).encode("utf-8")
        elif isinstance(value, str):
            serialized_val = value.encode("utf-8")
        else:
            serialized_val = value

        serialized_key = key.encode("utf-8") if key is not None else None

        # Format headers as list of (str, bytes)
        formatted_headers = None
        if headers:
            if isinstance(headers, dict):
                formatted_headers = [
                    (k, v.encode("utf-8") if isinstance(v, str) else v)
                    for k, v in headers.items()
                ]
            else:
                formatted_headers = headers

        # Publish with backpressure handling (BufferError)
        max_attempts = 10
        for attempt in range(max_attempts):
            try:
                self._producer.produce(
                    topic=topic,
                    value=serialized_val,
                    key=serialized_key,
                    headers=formatted_headers,
                    on_delivery=self._delivery_callback,
                )
                self.published_count += 1
                # Poll to serve delivery callbacks
                self._producer.poll(0)
                break
            except BufferError:
                logger.warning("Producer queue full; serving callbacks and backing off...")
                self._producer.poll(0.1)
                time.sleep(0.05 * (attempt + 1))
            except Exception as exc:
                self.failed_count += 1
                logger.error("Unexpected producer produce error on topic %s: %s", topic, exc)
                return False
        else:
            logger.error("Failed to produce message after %d backpressure retries", max_attempts)
            return False

        if sync:
            self._producer.flush(timeout=5.0)

        return True

    def publish_dlq(
        self,
        raw_payload: str | bytes,
        failure_reason: str,
        failed_field: Optional[str] = None,
        observed_value: Optional[str] = None,
        source: str = "ingestion",
    ) -> bool:
        """Route unparseable, malformed, or corrupt records to the DLQ topic."""
        envelope = {
            "source": source,
            "failure_reason": failure_reason,
            "failed_field": failed_field,
            "observed_value": observed_value,
            "quarantined_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "raw_payload": (
                raw_payload.decode("utf-8", errors="replace")
                if isinstance(raw_payload, bytes)
                else raw_payload
            ),
        }
        self.dlq_count += 1
        headers = {"x-flowsync-dlq-reason": failure_reason, "x-flowsync-source": source}
        return self.publish(topic=self.dlq_topic, value=envelope, headers=headers)

    def flush(self, timeout: float = 10.0) -> int:
        """Wait for all outstanding messages to be delivered.
        
        Returns remaining messages in queue (0 on complete success).
        """
        return self._producer.flush(timeout=timeout)

    def stats(self) -> Dict[str, Any]:
        """Return cumulative publishing and delivery statistics."""
        return {
            "published_count": self.published_count,
            "delivered_count": self.delivered_count,
            "failed_count": self.failed_count,
            "dlq_count": self.dlq_count,
            "last_delivery_error": self._last_delivery_error,
        }

