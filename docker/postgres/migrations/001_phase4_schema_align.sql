-- ==============================================================================
-- FlowSync Database Migration 001: Phase 4 Schema Alignment
-- Target: PostgreSQL 16
-- ==============================================================================

-- 1. Schema Migrations Ledger
CREATE TABLE IF NOT EXISTS schema_migrations (
    version VARCHAR(64) PRIMARY KEY,
    applied_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- 2. Align events_valid
-- Add facility_id to events_valid without dropping existing columns
ALTER TABLE events_valid ADD COLUMN IF NOT EXISTS facility_id VARCHAR(32);
-- Make device_type nullable or default to 'sensor' if not provided
ALTER TABLE events_valid ALTER COLUMN device_type DROP NOT NULL;

CREATE INDEX IF NOT EXISTS idx_events_valid_facility ON events_valid (facility_id);

-- 3. Align events_invalid
-- Add Kafka metadata and failure details
ALTER TABLE events_invalid ADD COLUMN IF NOT EXISTS kafka_topic VARCHAR(64);
ALTER TABLE events_invalid ADD COLUMN IF NOT EXISTS kafka_partition INT;
ALTER TABLE events_invalid ADD COLUMN IF NOT EXISTS kafka_offset BIGINT;
ALTER TABLE events_invalid ADD COLUMN IF NOT EXISTS failure_reason VARCHAR(64);
ALTER TABLE events_invalid ADD COLUMN IF NOT EXISTS failed_field VARCHAR(64);
ALTER TABLE events_invalid ADD COLUMN IF NOT EXISTS observed_value TEXT;
-- Alter raw_payload or violations if needed to ensure raw non-JSON text toleration
ALTER TABLE events_invalid ALTER COLUMN raw_payload DROP NOT NULL;
ALTER TABLE events_invalid ADD COLUMN IF NOT EXISTS raw_text TEXT;
ALTER TABLE events_invalid ALTER COLUMN violations DROP NOT NULL;

-- Create unique index on kafka coordinates to prevent duplicate quarantine inserts
CREATE UNIQUE INDEX IF NOT EXISTS idx_events_invalid_kafka_coord
ON events_invalid (kafka_topic, kafka_partition, kafka_offset)
WHERE kafka_topic IS NOT NULL AND kafka_partition IS NOT NULL AND kafka_offset IS NOT NULL;

-- 4. Align pipeline_windowed_metrics
-- Add device_id column and unique constraint for windowed metrics
ALTER TABLE pipeline_windowed_metrics ADD COLUMN IF NOT EXISTS device_id VARCHAR(32);
ALTER TABLE pipeline_windowed_metrics ALTER COLUMN device_type DROP NOT NULL;

CREATE UNIQUE INDEX IF NOT EXISTS idx_windowed_metrics_device_time
ON pipeline_windowed_metrics (window_start, window_end, device_id)
WHERE device_id IS NOT NULL;

-- 5. Create pipeline_batch_log
CREATE TABLE IF NOT EXISTS pipeline_batch_log (
    query_name VARCHAR(64) NOT NULL,
    generation VARCHAR(32) NOT NULL,
    batch_id BIGINT NOT NULL,
    input_rows INT NOT NULL DEFAULT 0,
    valid_rows INT NOT NULL DEFAULT 0,
    structural_reject_rows INT NOT NULL DEFAULT 0,
    status VARCHAR(32) NOT NULL,
    attempts INT NOT NULL DEFAULT 1,
    started_at TIMESTAMPTZ NOT NULL,
    finished_at TIMESTAMPTZ,
    PRIMARY KEY (query_name, generation, batch_id)
);

CREATE INDEX IF NOT EXISTS idx_batch_log_status ON pipeline_batch_log (status);
CREATE INDEX IF NOT EXISTS idx_batch_log_started ON pipeline_batch_log (started_at DESC);

-- Record migration execution
INSERT INTO schema_migrations (version) VALUES ('001_phase4_schema_align')
ON CONFLICT (version) DO NOTHING;

