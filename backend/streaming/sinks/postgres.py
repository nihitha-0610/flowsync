"""FlowSync - PostgreSQL Streaming Sink & Schema Mapper.

Provides single-point canonical-to-DDL column mapping, batch insertions,
idempotent deduplication (ON CONFLICT DO NOTHING), and windowed metric upserts.
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any, Dict, List, Optional
import psycopg
from psycopg.rows import dict_row

logger = logging.getLogger("flowsync.streaming.sinks.postgres")

# Single authoritative schema mapping dict between Canonical Event and PostgreSQL DDL
CANONICAL_TO_DDL_MAPPING: Dict[str, str] = {
    "event_id": "event_id",
    "device_id": "device_id",
    "facility_id": "facility_id",
    "timestamp": "timestamp",
    "temperature": "temperature",
    "vibration": "vibration",
    "pressure": "pressure",
    "flow_rate": "flow_rate",
    "power_consumption": "power_consumption",
    "status_code": "status_code",
    "location": "location",
}


class PostgresStreamingSink:
    """Handles high-throughput micro-batch relational persistence to PostgreSQL."""

    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        dbname: Optional[str] = None,
        user: Optional[str] = None,
        password: Optional[str] = None,
    ):
        self.host = host or os.getenv("POSTGRES_HOST", "postgres")
        self.port = port or int(os.getenv("POSTGRES_PORT", "5432"))
        self.dbname = dbname or os.getenv("POSTGRES_DB", "flowsync_db")
        self.user = user or os.getenv("POSTGRES_USER", "flowsync_user")
        self.password = password or os.getenv("POSTGRES_PASSWORD", "flowsync_secure_password")

    def get_connection(self) -> psycopg.Connection:
        """Create and return a new PostgreSQL database connection."""
        return psycopg.connect(
            host=self.host,
            port=self.port,
            dbname=self.dbname,
            user=self.user,
            password=self.password,
            autocommit=False,
        )

    def write_valid_events(self, rows: List[Dict[str, Any]]) -> int:
        """Insert valid telemetry events idempotently (ON CONFLICT DO NOTHING).
        
        Returns the count of successfully executed row operations.
        """
        if not rows:
            return 0

        insert_sql = """
            INSERT INTO events_valid (
                event_id, timestamp, device_id, facility_id, location,
                temperature, vibration, pressure, flow_rate, power_consumption,
                status_code, source, processed_at
            ) VALUES (
                %(event_id)s, %(timestamp)s, %(device_id)s, %(facility_id)s, %(location)s,
                %(temperature)s, %(vibration)s, %(pressure)s, %(flow_rate)s, %(power_consumption)s,
                %(status_code)s, %(source)s, CURRENT_TIMESTAMP
            )
            ON CONFLICT (event_id) DO NOTHING;
        """

        with self.get_connection() as conn:
            with conn.cursor() as cur:
                prepared_rows = []
                for r in rows:
                    row_copy = dict(r)
                    if "source" not in row_copy:
                        row_copy["source"] = "stream_processor"
                    prepared_rows.append(row_copy)

                cur.executemany(insert_sql, prepared_rows)
            conn.commit()

        logger.debug("Successfully persisted %d valid rows to events_valid", len(rows))
        return len(rows)

    def write_invalid_events(self, rows: List[Dict[str, Any]]) -> int:
        """Insert structural rejects and invalid records to events_invalid quarantine table."""
        if not rows:
            return 0

        insert_sql = """
            INSERT INTO events_invalid (
                event_id, timestamp, raw_payload, raw_text,
                kafka_topic, kafka_partition, kafka_offset,
                failure_stage, failure_reason, failed_field, observed_value,
                violations, validation_run_id, quarantined_at
            ) VALUES (
                %(event_id)s, %(timestamp)s, %(raw_payload)s, %(raw_text)s,
                %(kafka_topic)s, %(kafka_partition)s, %(kafka_offset)s,
                %(failure_stage)s, %(failure_reason)s, %(failed_field)s, %(observed_value)s,
                %(violations)s, %(validation_run_id)s, CURRENT_TIMESTAMP
            )
            ON CONFLICT (kafka_topic, kafka_partition, kafka_offset)
            WHERE kafka_topic IS NOT NULL AND kafka_partition IS NOT NULL AND kafka_offset IS NOT NULL
            DO NOTHING;
        """

        prepared_rows = []
        for r in rows:
            row_copy = dict(r)
            if "validation_run_id" not in row_copy:
                row_copy["validation_run_id"] = None
            payload = row_copy.get("raw_payload")
            row_copy["raw_text"] = payload if isinstance(payload, str) else (json.dumps(payload) if payload is not None else None)
            if isinstance(payload, str):
                try:
                    json.loads(payload)
                except Exception:
                    row_copy["raw_payload"] = None
            prepared_rows.append(row_copy)

        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.executemany(insert_sql, prepared_rows)
            conn.commit()

        logger.debug("Successfully quarantined %d rows to events_invalid", len(rows))
        return len(rows)

    def write_windowed_metrics(self, rows: List[Dict[str, Any]]) -> int:
        """Upsert windowed tumbling aggregated metrics into pipeline_windowed_metrics."""
        if not rows:
            return 0

        upsert_sql = """
            INSERT INTO pipeline_windowed_metrics (
                window_start, window_end, device_id,
                event_count, avg_temperature, max_temperature,
                avg_vibration, max_vibration, avg_pressure, created_at
            ) VALUES (
                %(window_start)s, %(window_end)s, %(device_id)s,
                %(event_count)s, %(avg_temperature)s, %(max_temperature)s,
                %(avg_vibration)s, %(max_vibration)s, %(avg_pressure)s,
                CURRENT_TIMESTAMP
            )
            ON CONFLICT (window_start, window_end, device_id)
            WHERE device_id IS NOT NULL
            DO UPDATE SET
                event_count = EXCLUDED.event_count,
                avg_temperature = EXCLUDED.avg_temperature,
                max_temperature = EXCLUDED.max_temperature,
                avg_vibration = EXCLUDED.avg_vibration,
                max_vibration = EXCLUDED.max_vibration,
                avg_pressure = EXCLUDED.avg_pressure,
                created_at = CURRENT_TIMESTAMP;
        """

        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.executemany(upsert_sql, rows)
            conn.commit()

        logger.debug("Successfully upserted %d windowed metric rows", len(rows))
        return len(rows)

    def log_micro_batch(
        self,
        query_name: str,
        generation: str,
        batch_id: int,
        input_rows: int,
        valid_rows: int,
        structural_reject_rows: int,
        status: str,
        started_at: Any,
        finished_at: Any,
    ):
        """Record micro-batch lifecycle execution audit in pipeline_batch_log."""
        upsert_sql = """
            INSERT INTO pipeline_batch_log (
                query_name, generation, batch_id, input_rows, valid_rows,
                structural_reject_rows, status, attempts, started_at, finished_at
            ) VALUES (
                %(query_name)s, %(generation)s, %(batch_id)s, %(input_rows)s, %(valid_rows)s,
                %(structural_reject_rows)s, %(status)s, 1, %(started_at)s, %(finished_at)s
            )
            ON CONFLICT (query_name, generation, batch_id)
            DO UPDATE SET
                input_rows = EXCLUDED.input_rows,
                valid_rows = EXCLUDED.valid_rows,
                structural_reject_rows = EXCLUDED.structural_reject_rows,
                status = EXCLUDED.status,
                attempts = pipeline_batch_log.attempts + 1,
                finished_at = EXCLUDED.finished_at;
        """

        data = {
            "query_name": query_name,
            "generation": generation,
            "batch_id": batch_id,
            "input_rows": input_rows,
            "valid_rows": valid_rows,
            "structural_reject_rows": structural_reject_rows,
            "status": status,
            "started_at": started_at,
            "finished_at": finished_at,
        }

        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(upsert_sql, data)
                conn.commit()
        except Exception as exc:
            logger.error("Failed to write to pipeline_batch_log: %s", exc)

    def register_suite(
        self,
        suite_name: str,
        suite_version: str,
        suite_fingerprint: str,
        expectation_count: int,
        canonical_rules: List[Dict[str, Any]],
    ):
        """Register expectation suite in data_quality_suite_registry."""
        sql = """
            INSERT INTO data_quality_suite_registry (
                suite_name, suite_version, suite_fingerprint,
                expectation_count, canonical_rules, is_active
            ) VALUES (
                %(suite_name)s, %(suite_version)s, %(suite_fingerprint)s,
                %(expectation_count)s, %(canonical_rules)s, TRUE
            )
            ON CONFLICT (suite_name, suite_version) DO UPDATE SET
                suite_fingerprint = EXCLUDED.suite_fingerprint,
                expectation_count = EXCLUDED.expectation_count,
                canonical_rules = EXCLUDED.canonical_rules,
                is_active = TRUE;
        """
        data = {
            "suite_name": suite_name,
            "suite_version": suite_version,
            "suite_fingerprint": suite_fingerprint,
            "expectation_count": expectation_count,
            "canonical_rules": json.dumps(canonical_rules),
        }
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, data)
            conn.commit()

    def record_data_quality_run(self, run_dict: Dict[str, Any]):
        """Persist data quality validation run to data_quality_runs."""
        sql = """
            INSERT INTO data_quality_runs (
                run_id, suite_name, batch_id, query_id, generation,
                suite_version, total_records, valid_records, invalid_records,
                success_rate, evaluation_time_ms, execution_status,
                quality_status, expectation_results, metadata, evaluated_at
            ) VALUES (
                %(run_id)s, %(suite_name)s, %(batch_id)s, %(query_id)s, %(generation)s,
                %(suite_version)s, %(total_records)s, %(valid_records)s, %(invalid_records)s,
                %(success_rate)s, %(evaluation_time_ms)s, %(execution_status)s,
                %(quality_status)s, %(expectation_results)s, %(metadata)s, CURRENT_TIMESTAMP
            )
            ON CONFLICT (run_id) WHERE run_id IS NOT NULL DO NOTHING;
        """
        payload = dict(run_dict)
        if isinstance(payload.get("expectation_results"), (list, dict)):
            payload["expectation_results"] = json.dumps(payload["expectation_results"])
        if isinstance(payload.get("metadata"), (list, dict)):
            payload["metadata"] = json.dumps(payload["metadata"])

        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, payload)
            conn.commit()

    def reserve_manifest_lease(
        self,
        query_id: str,
        generation: str,
        batch_id: int,
        attempt_id: str,
        lease_seconds: int = 60,
    ) -> int:
        """Reserve or renew a lease in pipeline_manifest_ledger with an atomic fencing token."""
        sql = """
            INSERT INTO pipeline_manifest_ledger (
                query_id, generation, batch_id, attempt_id, fencing_token,
                status, lease_expires_at, updated_at
            ) VALUES (
                %(query_id)s, %(generation)s, %(batch_id)s, %(attempt_id)s, 1,
                'RESERVED', CURRENT_TIMESTAMP + (%(lease_seconds)s || ' seconds')::INTERVAL, CURRENT_TIMESTAMP
            )
            ON CONFLICT (query_id, generation, batch_id) DO UPDATE SET
                attempt_id = EXCLUDED.attempt_id,
                fencing_token = pipeline_manifest_ledger.fencing_token + 1,
                status = 'RESERVED',
                lease_expires_at = CURRENT_TIMESTAMP + (%(lease_seconds)s || ' seconds')::INTERVAL,
                updated_at = CURRENT_TIMESTAMP
            RETURNING fencing_token;
        """
        data = {
            "query_id": query_id,
            "generation": generation,
            "batch_id": batch_id,
            "attempt_id": attempt_id,
            "lease_seconds": str(lease_seconds),
        }
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, data)
                token = cur.fetchone()[0]
            conn.commit()
        return token

    def commit_manifest(
        self,
        query_id: str,
        generation: str,
        batch_id: int,
        attempt_id: str,
        fencing_token: int,
        manifest_path: str,
        manifest_checksum: str,
    ):
        """Update manifest ledger state to MANIFEST_COMMITTED guarded by fencing token."""
        sql = """
            UPDATE pipeline_manifest_ledger
            SET status = 'MANIFEST_COMMITTED',
                manifest_path = %(manifest_path)s,
                manifest_checksum = %(manifest_checksum)s,
                updated_at = CURRENT_TIMESTAMP
            WHERE query_id = %(query_id)s
              AND generation = %(generation)s
              AND batch_id = %(batch_id)s
              AND attempt_id = %(attempt_id)s
              AND fencing_token = %(fencing_token)s;
        """
        data = {
            "query_id": query_id,
            "generation": generation,
            "batch_id": batch_id,
            "attempt_id": attempt_id,
            "fencing_token": fencing_token,
            "manifest_path": manifest_path,
            "manifest_checksum": manifest_checksum,
        }
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, data)
            conn.commit()

    def complete_batch(
        self,
        query_id: str,
        generation: str,
        batch_id: int,
        attempt_id: str,
        fencing_token: int,
    ):
        """Update manifest ledger state to BATCH_COMPLETED upon sink execution."""
        sql = """
            UPDATE pipeline_manifest_ledger
            SET status = 'BATCH_COMPLETED',
                updated_at = CURRENT_TIMESTAMP
            WHERE query_id = %(query_id)s
              AND generation = %(generation)s
              AND batch_id = %(batch_id)s
              AND attempt_id = %(attempt_id)s
              AND fencing_token = %(fencing_token)s;
        """
        data = {
            "query_id": query_id,
            "generation": generation,
            "batch_id": batch_id,
            "attempt_id": attempt_id,
            "fencing_token": fencing_token,
        }
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, data)
            conn.commit()
