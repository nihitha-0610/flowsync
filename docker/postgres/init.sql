-- ==============================================================================
-- FlowSync Database Initialization DDL
-- Target: PostgreSQL 16
-- Description: Creates operational, analytical, quarantine, and audit tables
-- ==============================================================================

-- Enable UUID extension for unique event and anomaly identification
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ------------------------------------------------------------------------------
-- 1. Valid Telemetry Records Table (events_valid)
-- Stores successfully validated sensor records ready for operational query
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS events_valid (
    id BIGSERIAL PRIMARY KEY,
    event_id UUID UNIQUE NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    device_id VARCHAR(32) NOT NULL,
    device_type VARCHAR(32),
    facility_id VARCHAR(32),
    location VARCHAR(64),
    temperature DOUBLE PRECISION NOT NULL,
    vibration DOUBLE PRECISION NOT NULL,
    pressure DOUBLE PRECISION NOT NULL,
    flow_rate DOUBLE PRECISION,
    power_consumption DOUBLE PRECISION,
    status_code VARCHAR(16) NOT NULL,
    source VARCHAR(32) DEFAULT 'generator',
    processed_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_events_valid_timestamp ON events_valid (timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_events_valid_device_time ON events_valid (device_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_events_valid_type ON events_valid (device_type);

-- ------------------------------------------------------------------------------
-- 2. Quarantined / Invalid Telemetry Records Table (events_invalid)
-- Preserves records failing Great Expectations validation with rule violations
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS events_invalid (
    id BIGSERIAL PRIMARY KEY,
    event_id UUID,
    timestamp TIMESTAMPTZ,
    raw_payload JSONB,
    raw_text TEXT,
    kafka_topic VARCHAR(64),
    kafka_partition INT,
    kafka_offset BIGINT,
    failure_stage VARCHAR(64) NOT NULL,
    failure_reason VARCHAR(64),
    failed_field VARCHAR(64),
    observed_value TEXT,
    violations JSONB,
    quarantined_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_events_invalid_kafka_coord
ON events_invalid (kafka_topic, kafka_partition, kafka_offset)
WHERE kafka_topic IS NOT NULL AND kafka_partition IS NOT NULL AND kafka_offset IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_events_invalid_timestamp ON events_invalid (quarantined_at DESC);
CREATE INDEX IF NOT EXISTS idx_events_invalid_stage ON events_invalid (failure_stage);

-- ------------------------------------------------------------------------------
-- 3. Data Quality Validation Run History (data_quality_runs)
-- Tracks batch validation metrics, pass rates, and evaluation performance
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS data_quality_runs (
    id BIGSERIAL PRIMARY KEY,
    suite_name VARCHAR(64) NOT NULL,
    batch_id VARCHAR(64) NOT NULL,
    total_records INT NOT NULL,
    valid_records INT NOT NULL,
    invalid_records INT NOT NULL,
    success_rate DOUBLE PRECISION NOT NULL,
    evaluation_time_ms DOUBLE PRECISION NOT NULL,
    evaluated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_dq_runs_evaluated_at ON data_quality_runs (evaluated_at DESC);

-- ------------------------------------------------------------------------------
-- 4. Windowed Aggregated Metrics Table (pipeline_windowed_metrics)
-- Tumbling-window sensor summaries computed by Spark Structured Streaming
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS pipeline_windowed_metrics (
    id BIGSERIAL PRIMARY KEY,
    window_start TIMESTAMPTZ NOT NULL,
    window_end TIMESTAMPTZ NOT NULL,
    device_type VARCHAR(32) NOT NULL,
    event_count INT NOT NULL,
    avg_temperature DOUBLE PRECISION,
    max_temperature DOUBLE PRECISION,
    avg_vibration DOUBLE PRECISION,
    max_vibration DOUBLE PRECISION,
    avg_pressure DOUBLE PRECISION,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_window_device UNIQUE (window_start, window_end, device_type)
);

CREATE INDEX IF NOT EXISTS idx_windowed_metrics_time ON pipeline_windowed_metrics (window_start DESC);

-- ------------------------------------------------------------------------------
-- 5. AI Anomaly Detections Table (anomaly_detections)
-- Stores Isolation Forest predictions, scores, and feature explainability drivers
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS anomaly_detections (
    id BIGSERIAL PRIMARY KEY,
    anomaly_id UUID UNIQUE NOT NULL DEFAULT uuid_generate_v4(),
    event_id UUID REFERENCES events_valid(event_id) ON DELETE CASCADE,
    device_id VARCHAR(32) NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    anomaly_score DOUBLE PRECISION NOT NULL,
    confidence DOUBLE PRECISION NOT NULL,
    is_anomaly BOOLEAN NOT NULL DEFAULT TRUE,
    primary_driver VARCHAR(64) NOT NULL,
    feature_contributions JSONB NOT NULL,
    detected_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_anomalies_timestamp ON anomaly_detections (timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_anomalies_device ON anomaly_detections (device_id);

-- ------------------------------------------------------------------------------
-- 6. Structured Streaming Micro-Batch Audit Log (pipeline_batch_log)
-- ------------------------------------------------------------------------------
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

-- ------------------------------------------------------------------------------
-- 7. Database Migration Ledger (schema_migrations)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS schema_migrations (
    version VARCHAR(64) PRIMARY KEY,
    applied_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO schema_migrations (version) VALUES ('000_init'), ('001_phase4_schema_align')
ON CONFLICT (version) DO NOTHING;

