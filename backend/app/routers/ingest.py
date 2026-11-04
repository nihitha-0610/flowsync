"""FlowSync - Event Ingestion API Router (Single & CSV Ingest)."""

from __future__ import annotations

import csv
import io
import json
import logging
import os
from typing import Any, Dict, List, Optional, Union
from fastapi import APIRouter, File, HTTPException, UploadFile

from core.event_contract import CanonicalTelemetryEvent

logger = logging.getLogger("flowsync.api.ingest")

router = APIRouter(prefix="/api/v1/ingest", tags=["Ingest"])

_producer: Any = None


def get_producer():
    """Lazy initialize Kafka producer."""
    global _producer
    if _producer is None:
        try:
            from ingestion.producer import KafkaEventProducer
            bootstrap = os.getenv("KAFKA_BOOTSTRAP_SERVERS") or os.getenv("KAFKA_BROKER_INTERNAL", "kafka:9092")
            _producer = KafkaEventProducer(bootstrap_servers=bootstrap)
        except Exception as exc:
            logger.error("Could not initialize Kafka producer: %s", exc)
            raise HTTPException(status_code=503, detail=f"Kafka producer unavailable: {exc}")
    return _producer


@router.post("")
def ingest_event(payload: Union[Dict[str, Any], List[Dict[str, Any]]]):
    """Ingest single or batch telemetry event and publish to Kafka events.raw topic."""
    records = payload if isinstance(payload, list) else [payload]
    producer = get_producer()
    topic = os.getenv("KAFKA_TOPIC_RAW", "events.raw")

    published = 0
    errors = []

    for r in records:
        try:
            event = CanonicalTelemetryEvent(**r)
            key = event.device_id
            value = event.to_json_str()
            producer.publish(topic=topic, key=key, value=value)
            published += 1
        except Exception as exc:
            errors.append({"record": r, "error": str(exc)})

    producer.flush(timeout=5.0)

    return {
        "status": "success" if published > 0 else "failed",
        "published_count": published,
        "failed_count": len(errors),
        "errors": errors[:10],
    }


@router.post("/csv")
async def ingest_csv(file: UploadFile = File(...)):
    """Upload CSV file containing sensor telemetry records and produce to Kafka."""
    content = await file.read()
    decoded = content.decode("utf-8")
    reader = csv.DictReader(io.StringIO(decoded))

    records = list(reader)
    producer = get_producer()
    topic = os.getenv("KAFKA_TOPIC_RAW", "events.raw")

    published = 0
    errors = []

    for r in records:
        try:
            for num_col in ["temperature", "vibration", "pressure", "flow_rate", "power_consumption"]:
                if num_col in r and r[num_col] != "":
                    r[num_col] = float(r[num_col])
                elif num_col in r:
                    r[num_col] = None

            event = CanonicalTelemetryEvent(**r)
            producer.publish(topic=topic, key=event.device_id, value=event.to_json_str())
            published += 1
        except Exception as exc:
            errors.append({"row": r, "error": str(exc)})

    producer.flush(timeout=5.0)

    return {
        "filename": file.filename,
        "total_rows": len(records),
        "published_count": published,
        "failed_count": len(errors),
        "errors": errors[:10],
    }
