export type NavPage =
  | 'overview'
  | 'ingestion'
  | 'explorer'
  | 'analytics'
  | 'quality'
  | 'anomalies'
  | 'monitoring'
  | 'storage';

export interface PipelineStats {
  valid_events_total: number;
  invalid_events_total: number;
  active_devices_total: number;
  anomalies_total: number;
  successful_microbatches: number;
}

export interface TelemetryEvent {
  id: number;
  event_id: string;
  timestamp: string;
  device_id: string;
  device_type?: string;
  facility_id: string;
  location: string;
  temperature: number;
  vibration: number;
  pressure: number;
  flow_rate?: number;
  power_consumption?: number;
  status_code: 'OK' | 'WARNING' | 'CRITICAL' | 'MAINTENANCE';
  source?: string;
  processed_at: string;
}

export interface InvalidEvent {
  id: number;
  event_id?: string;
  timestamp?: string;
  raw_payload?: any;
  raw_text?: string;
  kafka_topic?: string;
  kafka_partition?: number;
  kafka_offset?: number;
  failure_stage?: string;
  failure_reason?: string;
  failed_field?: string;
  observed_value?: string;
  violations?: any;
  validation_run_id?: string;
  quarantined_at: string;
}

export interface WindowMetric {
  id: number;
  window_start: string;
  window_end: string;
  device_id?: string;
  device_type?: string;
  event_count: number;
  avg_temperature: number;
  max_temperature: number;
  avg_vibration: number;
  max_vibration: number;
  avg_pressure: number;
  created_at: string;
}

export interface DataQualityRun {
  id: number;
  run_id: string;
  suite_name: string;
  batch_id: string;
  query_id: string;
  generation: string;
  suite_version: string;
  total_records: number;
  valid_records: number;
  invalid_records: number;
  success_rate: number;
  evaluation_time_ms: number;
  execution_status: string;
  quality_status: 'PASSED' | 'DEGRADED' | 'ERROR';
  expectation_results?: any[];
  metadata?: any;
  evaluated_at: string;
}

export interface CanonicalRule {
  type: string;
  kwargs: Record<string, any>;
}

export interface QualitySuite {
  suite_name: string;
  suite_version: string;
  suite_fingerprint: string;
  expectation_count: number;
  canonical_rules: CanonicalRule[];
  registered_at: string;
  is_active: boolean;
}

export interface ManifestRecord {
  query_id: string;
  generation: string;
  batch_id: number;
  attempt_id: string;
  fencing_token: number;
  status: string;
  manifest_path?: string;
  manifest_checksum?: string;
  lease_expires_at?: string;
  created_at: string;
  updated_at: string;
}

export interface AnomalyDetection {
  id: number;
  anomaly_id: string;
  event_id?: string;
  device_id: string;
  timestamp: string;
  anomaly_score: number;
  confidence: number;
  is_anomaly: boolean;
  primary_driver: string;
  feature_contributions: Record<string, number>;
  detected_at: string;
}
