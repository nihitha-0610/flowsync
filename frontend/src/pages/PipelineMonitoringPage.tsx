import React from 'react';
import {
  Activity,
  CheckCircle2,
  Cpu,
  Database,
  ExternalLink,
  HardDrive,
  Lock,
  Radio,
} from 'lucide-react';
import { PageHeader } from '../components/PageHeader';
import { ManifestRecord, PipelineStats } from '../types';

interface MonitoringPageProps {
  stats: PipelineStats | null;
  manifests: ManifestRecord[];
  isHealthy: boolean;
}

export const PipelineMonitoringPage: React.FC<MonitoringPageProps> = ({
  stats,
  manifests,
  isHealthy,
}) => {
  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <PageHeader
          pageId="monitoring"
          title="Pipeline Infrastructure & Fenced Manifest Ledger"
          description="Comprehensive audit of distributed streaming execution, KRaft broker coordination, PySpark state stores, and transactional fencing token leases."
        />
        <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg bg-[#FFFEFC] border border-[#DCD3C8] shadow-xs self-start">
          <span className={`w-2.5 h-2.5 rounded-full ${isHealthy ? 'bg-[#47745B] animate-pulse' : 'bg-[#A74449]'}`} />
          <span className="font-mono text-xs text-[#29272B] font-semibold">
            {isHealthy ? 'Backend Cluster Online' : 'Backend Disconnected'}
          </span>
        </div>
      </div>

      {/* 1. Infrastructure Service Health Mesh */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Kafka Broker */}
        <div className="p-4 rounded-xl bg-[#FFFEFC] border border-[#DCD3C8] shadow-xs flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between">
              <span className="font-heading font-bold text-xs text-[#29272B] flex items-center gap-1.5">
                <Radio className="w-3.5 h-3.5 text-[#64283D]" />
                Kafka 3.8.0 KRaft
              </span>
              <span className="w-2 h-2 rounded-full bg-[#47745B] animate-pulse"></span>
            </div>
            <div className="mt-2 font-mono text-[11px] text-[#77716D] space-y-0.5">
              <div>Broker: <strong className="text-[#29272B]">kafka:9092</strong></div>
              <div>Host Port: <strong className="text-[#29272B]">9094</strong></div>
              <div>Topic: <strong className="text-[#64283D]">events.raw</strong> (3 P)</div>
            </div>
          </div>
          <span className="mt-3 text-[10px] font-mono text-[#47745B] font-semibold">
            ● Ingress Stream Active
          </span>
        </div>

        {/* Spark Streaming */}
        <div className="p-4 rounded-xl bg-[#FFFEFC] border border-[#DCD3C8] shadow-xs flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between">
              <span className="font-heading font-bold text-xs text-[#29272B] flex items-center gap-1.5">
                <Cpu className="w-3.5 h-3.5 text-[#64283D]" />
                Spark Streaming 3.5.1
              </span>
              <span className="w-2 h-2 rounded-full bg-[#47745B] animate-pulse"></span>
            </div>
            <div className="mt-2 font-mono text-[11px] text-[#77716D] space-y-0.5">
              <div>Master: <strong className="text-[#29272B]">local[2]</strong></div>
              <div>Batches Committed: <strong className="text-[#64283D]">{stats?.successful_microbatches ?? 0}</strong></div>
              <div>Metrics: <strong className="text-[#29272B]">port 8001</strong></div>
            </div>
          </div>
          <span className="mt-3 text-[10px] font-mono text-[#47745B] font-semibold">
            ● Microbatches Processing
          </span>
        </div>

        {/* PostgreSQL 16 */}
        <div className="p-4 rounded-xl bg-[#FFFEFC] border border-[#DCD3C8] shadow-xs flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between">
              <span className="font-heading font-bold text-xs text-[#29272B] flex items-center gap-1.5">
                <Database className="w-3.5 h-3.5 text-[#64283D]" />
                PostgreSQL 16 DB
              </span>
              <span className="w-2 h-2 rounded-full bg-[#47745B] animate-pulse"></span>
            </div>
            <div className="mt-2 font-mono text-[11px] text-[#77716D] space-y-0.5">
              <div>Host: <strong className="text-[#29272B]">postgres:5432</strong></div>
              <div>Events Persisted: <strong className="text-[#64283D]">{stats?.valid_events_total ?? 0}</strong></div>
              <div>Isolation: <strong className="text-[#64283D]">Read Committed</strong></div>
            </div>
          </div>
          <span className="mt-3 text-[10px] font-mono text-[#47745B] font-semibold">
            ● ACID Relational Sinks
          </span>
        </div>

        {/* MinIO Object Lake */}
        <div className="p-4 rounded-xl bg-[#FFFEFC] border border-[#DCD3C8] shadow-xs flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between">
              <span className="font-heading font-bold text-xs text-[#29272B] flex items-center gap-1.5">
                <HardDrive className="w-3.5 h-3.5 text-[#64283D]" />
                MinIO S3a Lake
              </span>
              <span className="w-2 h-2 rounded-full bg-[#47745B] animate-pulse"></span>
            </div>
            <div className="mt-2 font-mono text-[11px] text-[#77716D] space-y-0.5">
              <div>API: <strong className="text-[#29272B]">minio:9000</strong></div>
              <div>Console: <strong className="text-[#29272B]">port 9001</strong></div>
              <div>Format: <strong className="text-[#64283D]">Snappy Parquet</strong></div>
            </div>
          </div>
          <span className="mt-3 text-[10px] font-mono text-[#47745B] font-semibold">
            ● 5 S3a Buckets Mounted
          </span>
        </div>
      </div>

      {/* 2. Observability & Telemetry Dashboards Links */}
      <div className="p-5 rounded-xl bg-[#FFFEFC] border border-[#DCD3C8] shadow-xs flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-lg bg-[#64283D] text-[#FFFEFC]">
            <Activity className="w-5 h-5 text-[#B08A59]" />
          </div>
          <div>
            <h3 className="font-heading font-bold text-sm text-[#29272B]">
              Integrated Observability Endpoints
            </h3>
            <p className="text-xs text-[#77716D] font-sans">
              Prometheus time-series metric scraper and Grafana operational monitoring dashboards.
            </p>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-3 text-xs">
          <a
            href="http://localhost:9090"
            target="_blank"
            rel="noreferrer"
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-[#F8F5F0] hover:bg-[#E9DFD2] border border-[#DCD3C8] text-[#29272B] font-semibold transition"
          >
            <span>Prometheus (9090)</span>
            <ExternalLink className="w-3.5 h-3.5 text-[#64283D]" />
          </a>

          <a
            href="http://localhost:3000"
            target="_blank"
            rel="noreferrer"
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-[#F8F5F0] hover:bg-[#E9DFD2] border border-[#DCD3C8] text-[#29272B] font-semibold transition"
          >
            <span>Grafana (3000)</span>
            <ExternalLink className="w-3.5 h-3.5 text-[#64283D]" />
          </a>

          <a
            href="http://localhost:8000/docs"
            target="_blank"
            rel="noreferrer"
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-[#64283D] hover:bg-[#4A1D2E] text-[#FFFEFC] font-semibold transition shadow-xs"
          >
            <span>FastAPI Swagger Docs</span>
            <ExternalLink className="w-3.5 h-3.5 text-[#B08A59]" />
          </a>
        </div>
      </div>

      {/* 3. Authoritative Fenced Manifest Ledger Audit Table */}
      <div className="rounded-xl border border-[#514850] bg-[#29272B] overflow-hidden shadow-md">
        <div className="px-5 py-3.5 border-b border-[#514850] bg-[#39343A] flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Lock className="w-4 h-4 text-[#B08A59]" />
            <h2 className="text-sm font-semibold text-[#FFFEFC] font-heading">
              Transactional Fenced Manifest Ledger (pipeline_manifest_ledger)
            </h2>
          </div>
          <span className="text-xs text-[#DCD3C8] font-mono">
            {manifests.length} batch ledger commits
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs font-mono text-[#EADDE2]">
            <thead className="bg-[#29272B] text-[#DCD3C8] uppercase text-[10px] tracking-wider border-b border-[#514850]">
              <tr>
                <th className="px-4 py-3">Batch ID</th>
                <th className="px-4 py-3">Query ID & Generation</th>
                <th className="px-4 py-3">Attempt ID</th>
                <th className="px-4 py-3">Fencing Token</th>
                <th className="px-4 py-3">Authoritative S3a Manifest Path</th>
                <th className="px-4 py-3">SHA-256 Checksum</th>
                <th className="px-4 py-3">Ledger Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#514850]/50">
              {manifests.length === 0 ? (
                <tr>
                  <td colSpan={7} className="px-4 py-8 text-center text-[#77716D] font-sans">
                    No manifest ledger commits recorded.
                  </td>
                </tr>
              ) : (
                manifests.map((m) => (
                  <tr key={`${m.query_id}-${m.batch_id}-${m.attempt_id}`} className="hover:bg-[#39343A]/70 transition">
                    <td className="px-4 py-2.5 font-bold text-[#B08A59]">
                      batch_{m.batch_id}
                    </td>
                    <td className="px-4 py-2.5 text-[#DCD3C8]">
                      {m.query_id} ({m.generation})
                    </td>
                    <td className="px-4 py-2.5 text-[#DCD3C8]">
                      {m.attempt_id}
                    </td>
                    <td className="px-4 py-2.5">
                      <span className="px-2 py-0.5 rounded font-bold bg-[#64283D]/40 text-[#EADDE2] border border-[#64283D]">
                        Token: {m.fencing_token}
                      </span>
                    </td>
                    <td className="px-4 py-2.5 text-[#DCD3C8] truncate max-w-xs" title={m.manifest_path}>
                      {m.manifest_path || '—'}
                    </td>
                    <td className="px-4 py-2.5 text-[#77716D] truncate max-w-[120px]" title={m.manifest_checksum}>
                      {m.manifest_checksum ? `${m.manifest_checksum.slice(0, 12)}...` : '—'}
                    </td>
                    <td className="px-4 py-2.5">
                      <span
                        className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded text-[10px] font-bold ${
                          m.status === 'BATCH_COMPLETED'
                            ? 'bg-[#47745B]/20 text-[#47745B] border border-[#47745B]/40'
                            : 'bg-[#A87531]/20 text-[#A87531] border border-[#A87531]/40'
                        }`}
                      >
                        <CheckCircle2 className="w-3 h-3" />
                        {m.status}
                      </span>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
