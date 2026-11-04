import {
  AnomalyDetection,
  DataQualityRun,
  InvalidEvent,
  ManifestRecord,
  PipelineStats,
  QualitySuite,
  TelemetryEvent,
  WindowMetric,
} from '../types';

const DIRECT_BACKEND = 'http://localhost:8000';

/**
 * Robust fetch wrapper that prioritizes the local Vite proxy (`/api`),
 * and transparently falls back to direct backend port 8000 if needed.
 */
async function fetchWithFallback(path: string, options?: RequestInit): Promise<Response> {
  try {
    const res = await fetch(path, options);
    const contentType = res.headers.get('content-type') || '';
    // If the proxy responds with valid JSON (or client error status), return it
    if ((res.ok && contentType.includes('application/json')) || (res.status >= 400 && res.status < 500)) {
      return res;
    }
  } catch {
    // Relative fetch failed (e.g. proxy unavailable or network refused); fall through to direct backend
  }

  // Fallback to direct backend URL
  const targetUrl = `${DIRECT_BACKEND}${path}`;
  return fetch(targetUrl, options);
}

export async function checkBackendHealth(): Promise<{ status: string; database?: boolean }> {
  try {
    const res = await fetchWithFallback('/health');
    if (!res.ok) return { status: 'down' };
    return res.json();
  } catch {
    return { status: 'down' };
  }
}

export async function fetchStats(): Promise<PipelineStats> {
  const res = await fetchWithFallback('/api/v1/events/stats');
  if (!res.ok) {
    const errText = await res.text().catch(() => res.statusText);
    throw new Error(`Failed to fetch pipeline stats (${res.status}): ${errText}`);
  }
  return res.json();
}

export async function fetchRecentEvents(limit = 100): Promise<TelemetryEvent[]> {
  const res = await fetchWithFallback(`/api/v1/events/recent?limit=${limit}`);
  if (!res.ok) {
    const errText = await res.text().catch(() => res.statusText);
    throw new Error(`Failed to fetch recent events (${res.status}): ${errText}`);
  }
  return res.json();
}

export async function fetchInvalidEvents(limit = 100): Promise<InvalidEvent[]> {
  const res = await fetchWithFallback(`/api/v1/events/invalid?limit=${limit}`);
  if (!res.ok) {
    const errText = await res.text().catch(() => res.statusText);
    throw new Error(`Failed to fetch invalid events (${res.status}): ${errText}`);
  }
  return res.json();
}

export async function fetchWindowMetrics(limit = 50): Promise<WindowMetric[]> {
  const res = await fetchWithFallback(`/api/v1/metrics/windows?limit=${limit}`);
  if (!res.ok) {
    const errText = await res.text().catch(() => res.statusText);
    throw new Error(`Failed to fetch window metrics (${res.status}): ${errText}`);
  }
  return res.json();
}

export async function fetchQualityRuns(limit = 30): Promise<DataQualityRun[]> {
  const res = await fetchWithFallback(`/api/v1/quality/runs?limit=${limit}`);
  if (!res.ok) {
    const errText = await res.text().catch(() => res.statusText);
    throw new Error(`Failed to fetch data quality runs (${res.status}): ${errText}`);
  }
  return res.json();
}

export async function fetchQualitySuites(): Promise<QualitySuite[]> {
  const res = await fetchWithFallback('/api/v1/quality/suites');
  if (!res.ok) {
    const errText = await res.text().catch(() => res.statusText);
    throw new Error(`Failed to fetch quality suites (${res.status}): ${errText}`);
  }
  return res.json();
}

export async function fetchManifests(limit = 30): Promise<ManifestRecord[]> {
  const res = await fetchWithFallback(`/api/v1/quality/manifests?limit=${limit}`);
  if (!res.ok) {
    const errText = await res.text().catch(() => res.statusText);
    throw new Error(`Failed to fetch manifest ledger (${res.status}): ${errText}`);
  }
  return res.json();
}

export async function fetchAnomalies(limit = 50): Promise<AnomalyDetection[]> {
  const res = await fetchWithFallback(`/api/v1/anomalies?limit=${limit}`);
  if (!res.ok) {
    const errText = await res.text().catch(() => res.statusText);
    throw new Error(`Failed to fetch anomalies (${res.status}): ${errText}`);
  }
  return res.json();
}

export async function ingestManualEvent(event: any): Promise<any> {
  const res = await fetchWithFallback('/api/v1/ingest', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(event),
  });
  if (!res.ok) {
    const errText = await res.text().catch(() => res.statusText);
    throw new Error(`Failed to ingest event (${res.status}): ${errText}`);
  }
  return res.json();
}
