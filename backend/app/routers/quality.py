"""FlowSync - Great Expectations Data Quality Endpoints."""

from __future__ import annotations

from typing import Any, Dict, List
from fastapi import APIRouter, Query

from app.database import execute_query

router = APIRouter(prefix="/api/v1/quality", tags=["Data Quality & Validation"])


@router.get("/runs")
def get_data_quality_runs(
    limit: int = Query(50, ge=1, le=500),
) -> List[Dict[str, Any]]:
    """Retrieve history of Great Expectations validation runs."""
    sql = """
        SELECT id, run_id, suite_name, batch_id, query_id, generation,
               suite_version, total_records, valid_records, invalid_records,
               success_rate, evaluation_time_ms, execution_status,
               quality_status, expectation_results, metadata, evaluated_at
        FROM data_quality_runs
        ORDER BY evaluated_at DESC
        LIMIT %s;
    """
    return execute_query(sql, (limit,))


@router.get("/suites")
def get_registered_suites() -> List[Dict[str, Any]]:
    """List registered expectation suites with fingerprints and rules."""
    sql = """
        SELECT suite_name, suite_version, suite_fingerprint,
               expectation_count, canonical_rules, registered_at, is_active
        FROM data_quality_suite_registry
        ORDER BY registered_at DESC;
    """
    return execute_query(sql)


@router.get("/manifests")
def get_manifest_ledger(limit: int = Query(50, ge=1, le=500)) -> List[Dict[str, Any]]:
    """Retrieve micro-batch manifest ledger audit records."""
    sql = """
        SELECT query_id, generation, batch_id, attempt_id, fencing_token,
               status, manifest_path, manifest_checksum, lease_expires_at,
               created_at, updated_at
        FROM pipeline_manifest_ledger
        ORDER BY created_at DESC
        LIMIT %s;
    """
    return execute_query(sql, (limit,))

