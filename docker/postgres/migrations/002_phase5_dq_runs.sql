-- ==============================================================================
-- FlowSync Database Migration 002: Phase 5 Data Quality Runs & Manifest Ledger
-- Target: PostgreSQL 16
-- ==============================================================================

-- 1. Data Quality Suite Registry Table
CREATE TABLE IF NOT EXISTS data_quality_suite_registry (
    suite_name VARCHAR(64) NOT NULL,
    suite_version VARCHAR(32) NOT NULL,
    suite_fingerprint VARCHAR(64) NOT NULL,
    expectation_count INT NOT NULL,
    canonical_rules JSONB NOT NULL,
    registered_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    PRIMARY KEY (suite_name, suite_version)
);

CREATE INDEX IF NOT EXISTS idx_suite_registry_active ON data_quality_suite_registry (suite_name, is_active);

-- 2. Pipeline Manifest Ledger Table (4-state machine with fencing token)
CREATE TABLE IF NOT EXISTS pipeline_manifest_ledger (
    query_id VARCHAR(64) NOT NULL,
    generation VARCHAR(32) NOT NULL,
    batch_id BIGINT NOT NULL,
    attempt_id VARCHAR(64) NOT NULL,
    fencing_token BIGINT NOT NULL DEFAULT 1,
    status VARCHAR(32) NOT NULL, -- RESERVED, MANIFEST_COMMITTED, BATCH_COMPLETED, FAILED
    manifest_path TEXT,
    manifest_checksum VARCHAR(64),
    lease_expires_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (query_id, generation, batch_id)
);

CREATE INDEX IF NOT EXISTS idx_manifest_ledger_status ON pipeline_manifest_ledger (status);
CREATE INDEX IF NOT EXISTS idx_manifest_ledger_lease ON pipeline_manifest_ledger (lease_expires_at);

-- 3. Upgrade data_quality_runs table
ALTER TABLE data_quality_runs ADD COLUMN IF NOT EXISTS run_id VARCHAR(64);
ALTER TABLE data_quality_runs ADD COLUMN IF NOT EXISTS query_id VARCHAR(64);
ALTER TABLE data_quality_runs ADD COLUMN IF NOT EXISTS generation VARCHAR(32);
ALTER TABLE data_quality_runs ADD COLUMN IF NOT EXISTS suite_version VARCHAR(32);
ALTER TABLE data_quality_runs ADD COLUMN IF NOT EXISTS execution_status VARCHAR(32) DEFAULT 'SUCCESS';
ALTER TABLE data_quality_runs ADD COLUMN IF NOT EXISTS quality_status VARCHAR(32);
ALTER TABLE data_quality_runs ADD COLUMN IF NOT EXISTS expectation_results JSONB;
ALTER TABLE data_quality_runs ADD COLUMN IF NOT EXISTS metadata JSONB;

-- Make run_id unique safely
CREATE UNIQUE INDEX IF NOT EXISTS idx_dq_runs_run_id ON data_quality_runs (run_id) WHERE run_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_dq_runs_query_batch ON data_quality_runs (query_id, generation, batch_id);

-- 4. Upgrade events_invalid table
ALTER TABLE events_invalid ADD COLUMN IF NOT EXISTS validation_run_id VARCHAR(64);
CREATE INDEX IF NOT EXISTS idx_events_invalid_validation_run_id ON events_invalid (validation_run_id) WHERE validation_run_id IS NOT NULL;

-- 5. Record migration in schema_migrations
INSERT INTO schema_migrations (version) VALUES ('002_phase5_dq_runs')
ON CONFLICT (version) DO NOTHING;

