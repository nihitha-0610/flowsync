"""FlowSync - Resilient Streaming CSV Ingestion Pipeline.

Processes uploaded CSV datasets line-by-line with UTF-8 BOM tolerance,
validates schema contracts, generates deterministic UUIDs, routes valid
records to Kafka events.raw and structural defects to events.dlq.
"""

from __future__ import annotations

import csv
import hashlib
import io
import logging
import os
import time
from dataclasses import dataclass
from typing import Any, Dict, Iterator, List, Optional, Tuple
from uuid import NAMESPACE_OID, uuid5

from core.config import get_settings
from core.event_contract import CanonicalTelemetryEvent, StatusCode
from ingestion.producer import KafkaEventProducer

logger = logging.getLogger("flowsync.ingestion.csv_ingest")


@dataclass
class CsvIngestResult:
    """Detailed summary of the CSV ingestion run."""
    total_rows: int
    valid_rows: int
    rejected_rows: int
    execution_time_seconds: float
    file_path: str


class CsvIngestionEngine:
    """High-throughput streaming CSV validator and Kafka dispatcher."""

    REQUIRED_HEADERS = {
        "device_id",
        "facility_id",
        "timestamp",
        "temperature",
        "vibration",
        "pressure",
        "flow_rate",
        "power_consumption",
        "status_code",
        "location",
    }

    def __init__(
        self,
        producer: Optional[KafkaEventProducer] = None,
        target_topic: Optional[str] = None,
        dlq_topic: Optional[str] = None,
    ):
        settings = get_settings()
        self.producer = producer or KafkaEventProducer()
        self.target_topic = target_topic or settings.KAFKA_TOPIC_RAW
        self.dlq_topic = dlq_topic or settings.KAFKA_TOPIC_DLQ

    def ingest_file(self, file_path: str, chunk_size: int = 1000) -> CsvIngestResult:
        """Stream a CSV file from disk, validate rows, and publish to Kafka."""
        start_time = time.perf_counter()
        total_rows = 0
        valid_rows = 0
        rejected_rows = 0

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"CSV file not found: {file_path}")

        # Compute file hash for deterministic event_id generation
        file_sha256 = self._compute_file_hash(file_path)

        with open(file_path, mode="r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            if reader.fieldnames is None:
                raise ValueError("CSV file is completely empty or missing header line")

            # Check header presence (strip whitespace)
            clean_headers = {h.strip() for h in reader.fieldnames if h}
            missing_headers = self.REQUIRED_HEADERS - clean_headers
            if missing_headers:
                raise ValueError(
                    f"CSV missing mandatory schema columns: {sorted(list(missing_headers))}"
                )

            for line_no, raw_row in enumerate(reader, start=2):
                total_rows += 1
                row = {k.strip(): v.strip() for k, v in raw_row.items() if k}

                # Generate deterministic UUID5 if event_id is missing or invalid
                event_id = row.get("event_id")
                if not event_id:
                    seed_str = f"{file_sha256}:{line_no}"
                    event_id = str(uuid5(NAMESPACE_OID, seed_str))
                    row["event_id"] = event_id

                # Attempt conversion and validation against CanonicalTelemetryEvent
                parsed_event, error_msg = self._validate_and_cast_row(row)

                if parsed_event:
                    valid_rows += 1
                    headers = {
                        "x-source": "csv_upload",
                        "x-file-path": os.path.basename(file_path),
                        "x-line-number": str(line_no),
                    }
                    self.producer.publish(
                        topic=self.target_topic,
                        value=parsed_event.to_canonical_dict(),
                        key=parsed_event.device_id,
                        headers=headers,
                    )
                else:
                    rejected_rows += 1
                    self.producer.publish_dlq(
                        raw_payload=str(raw_row),
                        failure_reason="csv_structural_validation_failed",
                        failed_field=None,
                        observed_value=error_msg,
                        source="csv_upload",
                    )

                if total_rows % chunk_size == 0:
                    self.producer.flush(timeout=2.0)
                    logger.info("Processed %d CSV rows (valid=%d, rejected=%d)", total_rows, valid_rows, rejected_rows)

        # Final flush
        self.producer.flush(timeout=5.0)
        elapsed = time.perf_counter() - start_time

        logger.info(
            "CSV ingestion complete for %s: %d total, %d valid, %d rejected in %.2fs",
            file_path,
            total_rows,
            valid_rows,
            rejected_rows,
            elapsed,
        )

        return CsvIngestResult(
            total_rows=total_rows,
            valid_rows=valid_rows,
            rejected_rows=rejected_rows,
            execution_time_seconds=round(elapsed, 3),
            file_path=file_path,
        )

    def _validate_and_cast_row(
        self, row: Dict[str, str]
    ) -> Tuple[Optional[CanonicalTelemetryEvent], Optional[str]]:
        """Attempt to cast string types and validate against canonical schema."""
        try:
            # Type casting from CSV string representations
            typed_dict = {
                "event_id": row["event_id"],
                "device_id": row["device_id"],
                "facility_id": row["facility_id"],
                "timestamp": row["timestamp"],
                "temperature": float(row["temperature"]),
                "vibration": float(row["vibration"]),
                "pressure": float(row["pressure"]),
                "flow_rate": float(row["flow_rate"]),
                "power_consumption": float(row["power_consumption"]),
                "status_code": row["status_code"],
                "location": row["location"],
            }
            event = CanonicalTelemetryEvent(**typed_dict)
            return event, None
        except Exception as exc:
            return None, str(exc)

    def _compute_file_hash(self, file_path: str) -> str:
        """Compute SHA256 of the first 64KB of the file for deterministic seeding."""
        hasher = hashlib.sha256()
        with open(file_path, "rb") as f:
            chunk = f.read(65536)
            hasher.update(chunk)
        return hasher.hexdigest()

