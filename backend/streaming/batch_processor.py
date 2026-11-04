"""FlowSync - Micro-Batch Multi-Sink Processor & Audit Orchestrator.

Implements the foreachBatch handler writing raw archives, refined Parquet lakes,
quarantine dead letters, Great Expectations validation, and transactional PostgreSQL sinks idempotently.
"""

from __future__ import annotations

import datetime
import hashlib
import json
import logging
import os
import time
import uuid
from typing import Any, Optional, Set

try:
    from pyspark.sql import DataFrame
    from pyspark.sql.functions import date_format
except ImportError:
    DataFrame = Any  # type: ignore
    date_format = Any  # type: ignore

from ml.inference import AnomalyInferenceService
from quality.runner import QualityRunner
from quality.suite import (
    CANONICAL_RULES,
    CANONICAL_SUITE_FINGERPRINT,
    SUITE_NAME,
    SUITE_VERSION,
)
from streaming.metrics import (
    STREAM_BATCH_DURATION,
    STREAM_INPUT_RATE,
    STREAM_PROCESSING_RATE,
    update_streaming_metrics,
)
from streaming.parsing import parse_and_validate_telemetry_stream
from streaming.sinks.postgres import PostgresStreamingSink

logger = logging.getLogger("flowsync.streaming.batch_processor")


class MicroBatchProcessor:
    """Orchestrates multi-destination idempotent sinks for Spark Structured Streaming."""

    def __init__(
        self,
        postgres_sink: Optional[PostgresStreamingSink] = None,
        raw_bucket: str = "flowsync-raw",
        refined_bucket: str = "flowsync-refined",
        quarantine_bucket: str = "flowsync-quarantine",
        query_name: str = "telemetry_stream_main",
    ):
        self.postgres_sink = postgres_sink or PostgresStreamingSink()
        self.raw_bucket = raw_bucket
        self.refined_bucket = refined_bucket
        self.quarantine_bucket = quarantine_bucket
        self.query_name = query_name
        self._committed_batches: Set[int] = set()
        self.quality_runner = QualityRunner(suite_name=SUITE_NAME, suite_version=SUITE_VERSION)
        self.anomaly_service = AnomalyInferenceService()

        # Register canonical quality suite in registry
        try:
            self.postgres_sink.register_suite(
                suite_name=SUITE_NAME,
                suite_version=SUITE_VERSION,
                suite_fingerprint=CANONICAL_SUITE_FINGERPRINT,
                expectation_count=len(CANONICAL_RULES),
                canonical_rules=CANONICAL_RULES,
            )
            logger.info("Registered canonical data quality suite '%s' (%s)", SUITE_NAME, SUITE_VERSION)
        except Exception as exc:
            logger.warning("Could not register suite on startup: %s", exc)

    def validate_batch_hook(self, valid_df: DataFrame, batch_id: int) -> DataFrame:
        """Pass-through validation hook for backward compatibility."""
        return valid_df

    def process_batch(self, batch_df: DataFrame, batch_id: int):
        """Primary foreachBatch sink handler executing all storage, quarantine, and audit tasks."""
        start_time = datetime.datetime.now(datetime.timezone.utc)
        start_perf = time.perf_counter()

        input_rows = batch_df.count()
        if input_rows == 0:
            duration_s = max(time.perf_counter() - start_perf, 0.0001)
            update_streaming_metrics(
                query_name=self.query_name,
                input_rows=0,
                processed_rows=0,
                rejected_rows=0,
                duration_seconds=duration_s,
                input_rate=0.0,
                processing_rate=0.0,
                is_retry=False,
            )
            logger.debug("Micro-batch %d is empty. Skipping processing.", batch_id)
            return

        logger.info("Processing micro-batch %d: %d incoming records", batch_id, input_rows)
        attempt_id = f"att_{uuid.uuid4().hex[:12]}"
        fencing_token = 1

        try:
            # 0. Reserve Lease in Manifest Ledger
            try:
                fencing_token = self.postgres_sink.reserve_manifest_lease(
                    query_id=self.query_name,
                    generation="v1",
                    batch_id=batch_id,
                    attempt_id=attempt_id,
                    lease_seconds=60,
                )
            except Exception as exc:
                logger.warning("Manifest lease reservation warning: %s", exc)

            # 1. Raw Archive Sink (MinIO S3A) - Idempotent overwrite keyed by batch_id
            raw_path = f"s3a://{self.raw_bucket}/batches/batch_{batch_id}.parquet"
            batch_df.write.mode("overwrite").format("parquet").option("compression", "snappy").save(raw_path)
            logger.debug("Micro-batch %d raw archive saved to %s", batch_id, raw_path)

            # 2. Parse, Cast & Structural Defect Isolation (Layer A & B)
            valid_df, structural_reject_df = parse_and_validate_telemetry_stream(batch_df)

            # 3. Layer C: Great Expectations Batch Validation Hook
            validated_df, gx_reject_df, dq_run_dict = self.quality_runner.validate_batch(
                df=valid_df,
                query_id=self.query_name,
                generation="v1",
                batch_id=batch_id,
            )
            valid_rows_count = validated_df.count()
            reject_rows_count = structural_reject_df.count()

            # 4. Manifest Publication & Manifest Ledger Commit
            manifest_obj = {
                "query_id": self.query_name,
                "generation": "v1",
                "batch_id": batch_id,
                "attempt_id": attempt_id,
                "fencing_token": fencing_token,
                "input_rows": input_rows,
                "valid_rows": valid_rows_count,
                "structural_reject_rows": reject_rows_count,
                "dq_run_id": dq_run_dict.get("run_id"),
                "dq_quality_status": dq_run_dict.get("quality_status"),
                "dq_success_rate": dq_run_dict.get("success_rate"),
                "committed_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            }
            manifest_json = json.dumps(manifest_obj, sort_keys=True)
            manifest_checksum = hashlib.sha256(manifest_json.encode("utf-8")).hexdigest()
            manifest_path = (
                f"s3a://{self.refined_bucket}/manifests/"
                f"batch_{self.query_name}_v1_{batch_id}_{attempt_id}_tok_{fencing_token}.json"
            )

            try:
                self.postgres_sink.commit_manifest(
                    query_id=self.query_name,
                    generation="v1",
                    batch_id=batch_id,
                    attempt_id=attempt_id,
                    fencing_token=fencing_token,
                    manifest_path=manifest_path,
                    manifest_checksum=manifest_checksum,
                )
            except Exception as exc:
                logger.warning("Manifest commit warning: %s", exc)

            # 5. Persist Data Quality Run to PostgreSQL
            try:
                self.postgres_sink.record_data_quality_run(dq_run_dict)
            except Exception as exc:
                logger.error("Failed to persist data quality run: %s", exc)

            # 6. Valid Storage Sinks
            if valid_rows_count > 0:
                # 6a. MinIO Refined Parquet Lake (Partitioned by date/hour)
                refined_path = f"s3a://{self.refined_bucket}/events"
                (
                    validated_df.withColumn("date", date_format("timestamp", "yyyy-MM-dd"))
                    .withColumn("hour", date_format("timestamp", "HH"))
                    .write.mode("append")
                    .format("parquet")
                    .option("compression", "snappy")
                    .partitionBy("date", "hour")
                    .save(refined_path)
                )

                # 6b. PostgreSQL events_valid Relational Sink (ON CONFLICT DO NOTHING)
                valid_records = [row.asDict() for row in validated_df.collect()]
                self.postgres_sink.write_valid_events(valid_records)

                # 6c. AI Anomaly Detection & Attribution (Phase 6)
                try:
                    self.anomaly_service.score_and_record(valid_records)
                except Exception as exc:
                    logger.warning("Anomaly detection scoring warning: %s", exc)

            # 7. Quarantine Storage Sinks
            if reject_rows_count > 0:
                # 7a. MinIO Quarantine Bucket
                quarantine_path = f"s3a://{self.quarantine_bucket}/structural_rejects/batch_{batch_id}.parquet"
                structural_reject_df.write.mode("overwrite").format("parquet").option("compression", "snappy").save(quarantine_path)

                # 7b. PostgreSQL events_invalid Table
                reject_records = []
                for row in structural_reject_df.collect():
                    d = row.asDict()
                    d["raw_text"] = d.get("raw_payload")
                    d["violations"] = None
                    d["validation_run_id"] = dq_run_dict.get("run_id")
                    reject_records.append(d)
                self.postgres_sink.write_invalid_events(reject_records)

            # 8. Complete Batch in Manifest Ledger
            try:
                self.postgres_sink.complete_batch(
                    query_id=self.query_name,
                    generation="v1",
                    batch_id=batch_id,
                    attempt_id=attempt_id,
                    fencing_token=fencing_token,
                )
            except Exception as exc:
                logger.warning("Batch completion ledger update warning: %s", exc)

            finished_time = datetime.datetime.now(datetime.timezone.utc)
            duration_s = max(time.perf_counter() - start_perf, 0.0001)
            input_rate = round(input_rows / duration_s, 2)
            processing_rate = round(valid_rows_count / duration_s, 2)

            # 9. Update Prometheus Metrics (with retry deduplication)
            is_retry = batch_id in self._committed_batches
            update_streaming_metrics(
                query_name=self.query_name,
                input_rows=input_rows,
                processed_rows=valid_rows_count,
                rejected_rows=reject_rows_count,
                duration_seconds=duration_s,
                input_rate=input_rate,
                processing_rate=processing_rate,
                is_retry=is_retry,
            )
            if not is_retry:
                self._committed_batches.add(batch_id)

            # 10. Audit Logging in pipeline_batch_log
            self.postgres_sink.log_micro_batch(
                query_name=self.query_name,
                generation="v1",
                batch_id=batch_id,
                input_rows=input_rows,
                valid_rows=valid_rows_count,
                structural_reject_rows=reject_rows_count,
                status="SUCCESS",
                started_at=start_time,
                finished_at=finished_time,
            )

            logger.info(
                "Completed micro-batch %d in %.2fs (Valid: %d, Rejected: %d, DQ: %s, Retry: %s)",
                batch_id,
                duration_s,
                valid_rows_count,
                reject_rows_count,
                dq_run_dict.get("quality_status"),
                is_retry,
            )

        except Exception as exc:
            finished_time = datetime.datetime.now(datetime.timezone.utc)
            duration_s = max(time.perf_counter() - start_perf, 0.0001)
            STREAM_BATCH_DURATION.labels(query_name=self.query_name).observe(duration_s)
            STREAM_INPUT_RATE.labels(query_name=self.query_name).set(0.0)
            STREAM_PROCESSING_RATE.labels(query_name=self.query_name).set(0.0)

            logger.error("Error processing micro-batch %d: %s", batch_id, exc, exc_info=True)
            self.postgres_sink.log_micro_batch(
                query_name=self.query_name,
                generation="v1",
                batch_id=batch_id,
                input_rows=input_rows,
                valid_rows=0,
                structural_reject_rows=0,
                status="FAILED",
                started_at=start_time,
                finished_at=finished_time,
            )
            raise exc
