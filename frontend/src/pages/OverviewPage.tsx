import React from 'react';
import {
  Activity,
  AlertTriangle,
  Archive,
  ArrowRight,
  CheckCircle2,
  Clock,
  Cpu,
  Database,
  Flame,
  LineChart,
  Send,
  Server,
  ShieldCheck,
} from 'lucide-react';
import { PageHeader } from '../components/PageHeader';
import { AnomalyDetection, NavPage, PipelineStats, TelemetryEvent } from '../types';

interface OverviewPageProps {
  stats: PipelineStats | null;
  events: TelemetryEvent[];
  anomalies: AnomalyDetection[];
  onNavigate: (page: NavPage) => void;
}

export const OverviewPage: React.FC<OverviewPageProps> = ({
  stats,
  events,
  anomalies,
  onNavigate,
}) => {
  const latestEvents = events.slice(0, 5);
  const latestAnomalies = anomalies.slice(0, 4);

  return (
    <div className="space-y-6">
      <PageHeader
        pageId="overview"
        title="Industrial Stream Intelligence Overview"
        description="Real-time operational dashboard synthesizing Kafka telemetry ingress, Spark micro-batch processing, Great Expectations verification, and AI anomaly detection."
        actions={
          <button
            onClick={() => onNavigate('ingestion')}
            className="flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-semibold bg-[#64283D] hover:bg-[#4A1D2E] text-[#FFFEFC] shadow-sm transition active:scale-95"
          >
            <Send className="w-3.5 h-3.5 text-[#B08A59]" />
            <span>Ingest New Telemetry</span>
          </button>
        }
      />

      {/* 1. Core KPIs */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
        {/* Valid Telemetry */}
        <div
          onClick={() => onNavigate('explorer')}
          className="p-5 rounded-xl bg-[#FFFEFC] border border-[#DCD3C8] shadow-xs hover:border-[#B08A59] transition cursor-pointer group"
        >
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-[#77716D]">Valid Telemetry</span>
            <div className="p-1.5 rounded-lg bg-[#47745B]/10 text-[#47745B]">
              <CheckCircle2 className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-2 text-2xl font-bold font-mono text-[#29272B]">
            {stats?.valid_events_total?.toLocaleString() ?? '—'}
          </div>
          <div className="mt-1 flex items-center justify-between text-[11px]">
            <span className="text-[#47745B] font-medium">PostgreSQL & S3a Lake</span>
            <ArrowRight className="w-3.5 h-3.5 text-[#77716D] opacity-0 group-hover:opacity-100 transition" />
          </div>
        </div>

        {/* Quarantined Rejects */}
        <div
          onClick={() => onNavigate('explorer')}
          className="p-5 rounded-xl bg-[#FFFEFC] border border-[#DCD3C8] shadow-xs hover:border-[#B08A59] transition cursor-pointer group"
        >
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-[#77716D]">Quarantined Rejects</span>
            <div className="p-1.5 rounded-lg bg-[#A87531]/10 text-[#A87531]">
              <AlertTriangle className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-2 text-2xl font-bold font-mono text-[#29272B]">
            {stats?.invalid_events_total?.toLocaleString() ?? '—'}
          </div>
          <div className="mt-1 flex items-center justify-between text-[11px]">
            <span className="text-[#A87531] font-medium">Dead Letter Queue</span>
            <ArrowRight className="w-3.5 h-3.5 text-[#77716D] opacity-0 group-hover:opacity-100 transition" />
          </div>
        </div>

        {/* AI Anomalies */}
        <div
          onClick={() => onNavigate('anomalies')}
          className="p-5 rounded-xl bg-[#FFFEFC] border border-[#DCD3C8] shadow-xs hover:border-[#B08A59] transition cursor-pointer group"
        >
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-[#77716D]">AI Anomalies</span>
            <div className="p-1.5 rounded-lg bg-[#A74449]/10 text-[#A74449]">
              <Flame className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-2 text-2xl font-bold font-mono text-[#29272B]">
            {stats?.anomalies_total?.toLocaleString() ?? '—'}
          </div>
          <div className="mt-1 flex items-center justify-between text-[11px]">
            <span className="text-[#A74449] font-medium">Isolation Forest Score</span>
            <ArrowRight className="w-3.5 h-3.5 text-[#77716D] opacity-0 group-hover:opacity-100 transition" />
          </div>
        </div>

        {/* Active Devices */}
        <div
          onClick={() => onNavigate('explorer')}
          className="p-5 rounded-xl bg-[#FFFEFC] border border-[#DCD3C8] shadow-xs hover:border-[#B08A59] transition cursor-pointer group"
        >
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-[#77716D]">Active Devices</span>
            <div className="p-1.5 rounded-lg bg-[#B08A59]/10 text-[#B08A59]">
              <Cpu className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-2 text-2xl font-bold font-mono text-[#29272B]">
            {stats?.active_devices_total?.toLocaleString() ?? '—'}
          </div>
          <div className="mt-1 flex items-center justify-between text-[11px]">
            <span className="text-[#B08A59] font-medium">Edge IoT Telemetry</span>
            <ArrowRight className="w-3.5 h-3.5 text-[#77716D] opacity-0 group-hover:opacity-100 transition" />
          </div>
        </div>

        {/* Committed Batches */}
        <div
          onClick={() => onNavigate('monitoring')}
          className="p-5 rounded-xl bg-[#FFFEFC] border border-[#DCD3C8] shadow-xs hover:border-[#B08A59] transition cursor-pointer group"
        >
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-[#77716D]">Committed Batches</span>
            <div className="p-1.5 rounded-lg bg-[#52758B]/10 text-[#52758B]">
              <Server className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-2 text-2xl font-bold font-mono text-[#29272B]">
            {stats?.successful_microbatches?.toLocaleString() ?? '—'}
          </div>
          <div className="mt-1 flex items-center justify-between text-[11px]">
            <span className="text-[#52758B] font-medium">Fenced Manifest Ledger</span>
            <ArrowRight className="w-3.5 h-3.5 text-[#77716D] opacity-0 group-hover:opacity-100 transition" />
          </div>
        </div>
      </div>

      {/* 2. Platform Architecture Health & Throughput Status */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Architecture Services */}
        <div className="lg:col-span-2 p-6 rounded-xl bg-[#FFFEFC] border border-[#DCD3C8] shadow-xs">
          <div className="flex items-center justify-between mb-4 pb-3 border-b border-[#DCD3C8]">
            <div className="flex items-center gap-2">
              <Activity className="w-4 h-4 text-[#64283D]" />
              <h3 className="font-heading font-bold text-sm text-[#29272B]">
                Pipeline Architecture & Invariant Health
              </h3>
            </div>
            <span className="px-2 py-0.5 rounded text-[11px] font-mono bg-[#47745B]/10 text-[#47745B] border border-[#47745B]/20">
              Zero Uncommitted Writes
            </span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
            <div className="p-3.5 rounded-lg bg-[#F8F5F0] border border-[#DCD3C8]">
              <div className="flex items-center justify-between">
                <span className="text-[11px] font-semibold text-[#64283D]">Kafka 3.8.0 KRaft</span>
                <span className="w-2 h-2 rounded-full bg-[#47745B]"></span>
              </div>
              <p className="text-[11px] text-[#77716D] mt-1">Topic: <code className="font-mono text-[#29272B]">events.raw</code></p>
              <p className="text-[10px] text-[#77716D] mt-0.5">3 Partitions • 24h retention</p>
            </div>

            <div className="p-3.5 rounded-lg bg-[#F8F5F0] border border-[#DCD3C8]">
              <div className="flex items-center justify-between">
                <span className="text-[11px] font-semibold text-[#64283D]">PySpark 3.5.1</span>
                <span className="w-2 h-2 rounded-full bg-[#47745B]"></span>
              </div>
              <p className="text-[11px] text-[#77716D] mt-1">Structured Streaming Engine</p>
              <p className="text-[10px] text-[#77716D] mt-0.5">Trigger 2.0s • Watermark 10s</p>
            </div>

            <div className="p-3.5 rounded-lg bg-[#F8F5F0] border border-[#DCD3C8]">
              <div className="flex items-center justify-between">
                <span className="text-[11px] font-semibold text-[#64283D]">Great Expectations</span>
                <span className="w-2 h-2 rounded-full bg-[#47745B]"></span>
              </div>
              <p className="text-[11px] text-[#77716D] mt-1">Suite: <code className="font-mono text-[#29272B]">canonical_v1</code></p>
              <p className="text-[10px] text-[#77716D] mt-0.5">19 Rules • Layer B/C Validated</p>
            </div>

            <div className="p-3.5 rounded-lg bg-[#F8F5F0] border border-[#DCD3C8]">
              <div className="flex items-center justify-between">
                <span className="text-[11px] font-semibold text-[#64283D]">Isolation Forest</span>
                <span className="w-2 h-2 rounded-full bg-[#47745B]"></span>
              </div>
              <p className="text-[11px] text-[#77716D] mt-1">Scikit-learn Anomaly Model</p>
              <p className="text-[10px] text-[#77716D] mt-0.5">Stored in MinIO S3a Models</p>
            </div>

            <div className="p-3.5 rounded-lg bg-[#F8F5F0] border border-[#DCD3C8]">
              <div className="flex items-center justify-between">
                <span className="text-[11px] font-semibold text-[#64283D]">PostgreSQL 16</span>
                <span className="w-2 h-2 rounded-full bg-[#47745B]"></span>
              </div>
              <p className="text-[11px] text-[#77716D] mt-1">ACID Relational Storage</p>
              <p className="text-[10px] text-[#77716D] mt-0.5">Fenced Manifest Ledger</p>
            </div>

            <div className="p-3.5 rounded-lg bg-[#F8F5F0] border border-[#DCD3C8]">
              <div className="flex items-center justify-between">
                <span className="text-[11px] font-semibold text-[#64283D]">MinIO Parquet Lake</span>
                <span className="w-2 h-2 rounded-full bg-[#47745B]"></span>
              </div>
              <p className="text-[11px] text-[#77716D] mt-1">Snappy-Compressed Batches</p>
              <p className="text-[10px] text-[#77716D] mt-0.5">Date / Hour Partitioned</p>
            </div>
          </div>
        </div>

        {/* Enterprise Quick Jump Directory */}
        <div className="p-6 rounded-xl bg-[#FFFEFC] border border-[#DCD3C8] shadow-xs flex flex-col justify-between">
          <div>
            <h3 className="font-heading font-bold text-sm text-[#29272B] mb-1">
              Enterprise Quick Navigation
            </h3>
            <p className="text-xs text-[#77716D] mb-4 font-sans">
              Direct access to dedicated platform workspaces.
            </p>

            <div className="space-y-2 text-xs">
              <button
                onClick={() => onNavigate('ingestion')}
                className="w-full flex items-center justify-between p-2.5 rounded-lg bg-[#F8F5F0] hover:bg-[#E9DFD2] border border-[#DCD3C8] text-[#29272B] font-medium transition"
              >
                <div className="flex items-center gap-2">
                  <Send className="w-3.5 h-3.5 text-[#64283D]" />
                  <span>Manual Ingest & Simulation</span>
                </div>
                <ArrowRight className="w-3.5 h-3.5 text-[#77716D]" />
              </button>

              <button
                onClick={() => onNavigate('explorer')}
                className="w-full flex items-center justify-between p-2.5 rounded-lg bg-[#F8F5F0] hover:bg-[#E9DFD2] border border-[#DCD3C8] text-[#29272B] font-medium transition"
              >
                <div className="flex items-center gap-2">
                  <Database className="w-3.5 h-3.5 text-[#64283D]" />
                  <span>Event Stream Explorer</span>
                </div>
                <ArrowRight className="w-3.5 h-3.5 text-[#77716D]" />
              </button>

              <button
                onClick={() => onNavigate('analytics')}
                className="w-full flex items-center justify-between p-2.5 rounded-lg bg-[#F8F5F0] hover:bg-[#E9DFD2] border border-[#DCD3C8] text-[#29272B] font-medium transition"
              >
                <div className="flex items-center gap-2">
                  <LineChart className="w-3.5 h-3.5 text-[#64283D]" />
                  <span>Tumbling Window Analytics</span>
                </div>
                <ArrowRight className="w-3.5 h-3.5 text-[#77716D]" />
              </button>

              <button
                onClick={() => onNavigate('quality')}
                className="w-full flex items-center justify-between p-2.5 rounded-lg bg-[#F8F5F0] hover:bg-[#E9DFD2] border border-[#DCD3C8] text-[#29272B] font-medium transition"
              >
                <div className="flex items-center gap-2">
                  <ShieldCheck className="w-3.5 h-3.5 text-[#64283D]" />
                  <span>Great Expectations Suite</span>
                </div>
                <ArrowRight className="w-3.5 h-3.5 text-[#77716D]" />
              </button>

              <button
                onClick={() => onNavigate('storage')}
                className="w-full flex items-center justify-between p-2.5 rounded-lg bg-[#F8F5F0] hover:bg-[#E9DFD2] border border-[#DCD3C8] text-[#29272B] font-medium transition"
              >
                <div className="flex items-center gap-2">
                  <Archive className="w-3.5 h-3.5 text-[#64283D]" />
                  <span>MinIO Lake & Manifest Ledger</span>
                </div>
                <ArrowRight className="w-3.5 h-3.5 text-[#77716D]" />
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* 3. Real-Time Activity Streams: Recent Telemetry & Latest Anomalies */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Ingested Telemetry Feed */}
        <div className="p-6 rounded-xl bg-[#29272B] border border-[#514850] shadow-md flex flex-col">
          <div className="flex items-center justify-between mb-4 pb-3 border-b border-[#514850]">
            <div className="flex items-center gap-2">
              <Database className="w-4 h-4 text-[#B08A59]" />
              <h3 className="font-heading font-bold text-sm text-[#FFFEFC]">
                Live Telemetry Ingress Stream
              </h3>
            </div>
            <button
              onClick={() => onNavigate('explorer')}
              className="text-xs text-[#B08A59] hover:underline flex items-center gap-1 font-mono"
            >
              <span>View all ({events.length})</span>
              <ArrowRight className="w-3 h-3" />
            </button>
          </div>

          <div className="overflow-x-auto flex-1">
            <table className="w-full text-left text-xs font-mono text-[#EADDE2]">
              <thead className="text-[10px] uppercase text-[#DCD3C8] border-b border-[#514850]">
                <tr>
                  <th className="pb-2">Time</th>
                  <th className="pb-2">Device</th>
                  <th className="pb-2">Temp</th>
                  <th className="pb-2">Vibe</th>
                  <th className="pb-2">Press</th>
                  <th className="pb-2">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#514850]/50">
                {latestEvents.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="py-6 text-center text-[#77716D] font-sans">
                      No telemetry ingested yet.
                    </td>
                  </tr>
                ) : (
                  latestEvents.map((ev) => (
                    <tr key={ev.event_id} className="hover:bg-[#39343A]/60 transition">
                      <td className="py-2.5 text-[#DCD3C8]">
                        {new Date(ev.timestamp).toLocaleTimeString()}
                      </td>
                      <td className="py-2.5 font-bold text-[#B08A59]">{ev.device_id}</td>
                      <td className="py-2.5">{ev.temperature.toFixed(1)}°C</td>
                      <td className="py-2.5">{ev.vibration.toFixed(2)}</td>
                      <td className="py-2.5">{ev.pressure.toFixed(1)}</td>
                      <td className="py-2.5">
                        <span
                          className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                            ev.status_code === 'OK'
                              ? 'bg-[#47745B]/20 text-[#47745B] border border-[#47745B]/40'
                              : ev.status_code === 'WARNING'
                              ? 'bg-[#A87531]/20 text-[#A87531] border border-[#A87531]/40'
                              : 'bg-[#A74449]/20 text-[#A74449] border border-[#A74449]/40'
                          }`}
                        >
                          {ev.status_code}
                        </span>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Latest AI Anomalies Detected */}
        <div className="p-6 rounded-xl bg-[#29272B] border border-[#514850] shadow-md flex flex-col">
          <div className="flex items-center justify-between mb-4 pb-3 border-b border-[#514850]">
            <div className="flex items-center gap-2">
              <Flame className="w-4 h-4 text-[#A74449]" />
              <h3 className="font-heading font-bold text-sm text-[#FFFEFC]">
                Isolation Forest Outlier Alerts
              </h3>
            </div>
            <button
              onClick={() => onNavigate('anomalies')}
              className="text-xs text-[#B08A59] hover:underline flex items-center gap-1 font-mono"
            >
              <span>View all ({anomalies.length})</span>
              <ArrowRight className="w-3 h-3" />
            </button>
          </div>

          <div className="space-y-3 flex-1 overflow-y-auto">
            {latestAnomalies.length === 0 ? (
              <div className="py-8 text-center text-[#77716D] text-xs font-sans">
                Operating strictly within nominal sensor distribution.
              </div>
            ) : (
              latestAnomalies.map((a) => (
                <div
                  key={a.anomaly_id}
                  className="p-3.5 rounded-lg bg-[#39343A] border border-[#514850] flex items-center justify-between text-xs"
                >
                  <div>
                    <div className="flex items-center gap-2 font-mono">
                      <span className="font-bold text-[#FFFEFC]">{a.device_id}</span>
                      <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-[#A74449]/20 text-[#A74449] border border-[#A74449]/40">
                        ANOMALY
                      </span>
                      <span className="text-[#DCD3C8]">
                        Score: {a.anomaly_score.toFixed(3)}
                      </span>
                    </div>
                    <div className="mt-1 text-[11px] text-[#77716D] font-sans">
                      Primary attribution driver:{' '}
                      <strong className="text-[#B08A59] font-mono">{a.primary_driver}</strong>
                    </div>
                  </div>
                  <span className="text-[11px] font-mono text-[#77716D] flex items-center gap-1">
                    <Clock className="w-3 h-3" />
                    {new Date(a.timestamp).toLocaleTimeString()}
                  </span>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

