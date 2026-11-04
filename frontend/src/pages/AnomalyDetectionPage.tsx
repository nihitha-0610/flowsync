import React, { useState } from 'react';
import {
  BrainCircuit,
  Clock,
  Flame,
  Info,
  Search,
  X,
} from 'lucide-react';
import { PageHeader } from '../components/PageHeader';
import { AnomalyDetection } from '../types';

interface AnomalyPageProps {
  anomalies: AnomalyDetection[];
}

export const AnomalyDetectionPage: React.FC<AnomalyPageProps> = ({ anomalies }) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [driverFilter, setDriverFilter] = useState('ALL');
  const [selectedAnomaly, setSelectedAnomaly] = useState<AnomalyDetection | null>(null);

  const drivers = Array.from(new Set(anomalies.map((a) => a.primary_driver)));

  const filteredAnomalies = anomalies.filter((a) => {
    const matchesSearch =
      a.device_id.toLowerCase().includes(searchQuery.toLowerCase()) ||
      a.primary_driver.toLowerCase().includes(searchQuery.toLowerCase()) ||
      a.anomaly_id.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesDriver = driverFilter === 'ALL' || a.primary_driver === driverFilter;
    return matchesSearch && matchesDriver;
  });

  const getSeverityBadge = (a: AnomalyDetection) => {
    if (a.anomaly_score >= 0.6 || (a.feature_contributions?.vibration && a.feature_contributions.vibration > 15)) {
      return (
        <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-[#A74449]/20 text-[#A74449] border border-[#A74449]/40">
          CRITICAL OUTLIER
        </span>
      );
    }
    if (a.anomaly_score >= 0.52) {
      return (
        <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-[#A87531]/20 text-[#A87531] border border-[#A87531]/40">
          MODERATE DRIFT
        </span>
      );
    }
    return (
      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-[#B08A59]/20 text-[#B08A59] border border-[#B08A59]/40">
        ELEVATED ANOMALY
      </span>
    );
  };

  return (
    <div className="space-y-6">
      <PageHeader
        pageId="anomalies"
        title="AI Anomaly Detection & Statistical Explainability"
        description="Unsupervised Isolation Forest model scored in real time during Spark micro-batch execution. Each outlier is attributed to individual dimensional drivers via standardized deviation contributions (σ-score)."
      />

      {/* 1. Model & Anomaly Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="p-4 rounded-xl bg-[#FFFEFC] border border-[#DCD3C8] shadow-xs">
          <span className="text-xs font-medium text-[#77716D]">Total Outliers Flagged</span>
          <div className="mt-1.5 text-2xl font-bold font-mono text-[#A74449]">
            {anomalies.length}
          </div>
          <span className="text-[11px] text-[#77716D]">Persisted to anomaly_detections</span>
        </div>

        <div className="p-4 rounded-xl bg-[#FFFEFC] border border-[#DCD3C8] shadow-xs">
          <span className="text-xs font-medium text-[#77716D]">Model Architecture</span>
          <div className="mt-1.5 text-lg font-bold font-heading text-[#64283D]">
            Isolation Forest
          </div>
          <span className="text-[11px] text-[#77716D] font-mono">100 Estimators • Contam 0.05</span>
        </div>

        <div className="p-4 rounded-xl bg-[#FFFEFC] border border-[#DCD3C8] shadow-xs">
          <span className="text-xs font-medium text-[#77716D]">Model Artifact Location</span>
          <div className="mt-1.5 text-xs font-bold font-mono text-[#29272B] truncate" title="s3a://flowsync-models/isolation_forest/v1/model.joblib">
            s3a://flowsync-models/.../model.joblib
          </div>
          <span className="text-[11px] text-[#47745B] font-medium">MinIO Storage Lake</span>
        </div>

        <div className="p-4 rounded-xl bg-[#FFFEFC] border border-[#DCD3C8] shadow-xs">
          <span className="text-xs font-medium text-[#77716D]">Max Anomaly Score</span>
          <div className="mt-1.5 text-2xl font-bold font-mono text-[#A87531]">
            {Math.max(...anomalies.map((a) => a.anomaly_score), 0).toFixed(3)}
          </div>
          <span className="text-[11px] text-[#77716D]">Confidence: ~96.1%</span>
        </div>
      </div>

      {/* 2. Search & Driver Filters */}
      <div className="p-4 rounded-xl bg-[#FFFEFC] border border-[#DCD3C8] shadow-xs flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex items-center gap-2">
          <BrainCircuit className="w-4 h-4 text-[#64283D]" />
          <span className="text-xs font-semibold text-[#29272B]">
            Anomaly Feed Explorer
          </span>
          <span className="px-2 py-0.5 rounded-full text-[10px] font-mono bg-[#EADDE2] text-[#64283D]">
            {filteredAnomalies.length} records
          </span>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <div className="relative min-w-[240px]">
            <Search className="w-3.5 h-3.5 text-[#77716D] absolute left-3 top-2.5" />
            <input
              type="text"
              placeholder="Filter by device or driver..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-8 pr-3 py-1.5 text-xs bg-[#F8F5F0] border border-[#DCD3C8] rounded-lg text-[#29272B] font-mono focus:border-[#64283D] focus:outline-none"
            />
          </div>

          <div className="flex items-center gap-1.5 text-xs">
            <span className="text-[#77716D]">Primary Driver:</span>
            <select
              value={driverFilter}
              onChange={(e) => setDriverFilter(e.target.value)}
              className="bg-[#F8F5F0] border border-[#DCD3C8] rounded-lg px-2.5 py-1.5 text-xs text-[#29272B] focus:outline-none focus:border-[#64283D]"
            >
              <option value="ALL">All Drivers</option>
              {drivers.map((d) => (
                <option key={d} value={d}>{d}</option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* 3. Detailed Anomalies List Cards */}
      <div className="space-y-3">
        {filteredAnomalies.length === 0 ? (
          <div className="p-12 text-center text-[#77716D] text-xs bg-[#FFFEFC] rounded-xl border border-[#DCD3C8]">
            No anomalies match the current filter.
          </div>
        ) : (
          filteredAnomalies.map((a) => (
            <div
              key={a.anomaly_id}
              onClick={() => setSelectedAnomaly(a)}
              className="p-5 rounded-xl bg-[#FFFEFC] border border-[#DCD3C8] shadow-xs hover:border-[#64283D] transition cursor-pointer flex flex-col md:flex-row md:items-center justify-between gap-4"
            >
              <div className="space-y-2">
                <div className="flex flex-wrap items-center gap-2.5">
                  <span className="font-mono font-bold text-sm text-[#29272B]">
                    {a.device_id}
                  </span>
                  {getSeverityBadge(a)}
                  <span className="text-xs font-mono text-[#77716D]">
                    Score: <strong className="text-[#A74449]">{a.anomaly_score.toFixed(3)}</strong>
                  </span>
                  <span className="text-xs font-mono text-[#77716D]">
                    Confidence: <strong className="text-[#47745B]">{(a.confidence * 100).toFixed(1)}%</strong>
                  </span>
                </div>

                <div className="text-xs text-[#29272B] flex items-center gap-2">
                  <span className="text-[#77716D]">Primary Explanation Driver:</span>
                  <span className="px-2 py-0.5 rounded font-mono font-bold uppercase text-[10px] bg-[#B08A59]/15 text-[#B08A59] border border-[#B08A59]/30">
                    {a.primary_driver}
                  </span>
                </div>

                {/* Statistical Feature Deviation Pills */}
                <div className="flex flex-wrap gap-2 pt-1 font-mono text-[10px]">
                  {Object.entries(a.feature_contributions || {}).map(([feat, dev]) => (
                    <span
                      key={feat}
                      className="px-2 py-0.5 rounded bg-[#F8F5F0] border border-[#DCD3C8] text-[#29272B]"
                    >
                      {feat}:{' '}
                      <strong className={Number(dev) > 10 ? 'text-[#A74449]' : 'text-[#A87531]'}>
                        {dev}σ
                      </strong>
                    </span>
                  ))}
                </div>
              </div>

              <div className="flex flex-col items-start md:items-end justify-between font-mono text-xs text-[#77716D] gap-2 shrink-0">
                <div className="flex items-center gap-1.5">
                  <Clock className="w-3.5 h-3.5" />
                  <span>{new Date(a.timestamp).toLocaleString()}</span>
                </div>
                <span className="text-[10px] text-[#77716D] truncate max-w-[180px]" title={a.anomaly_id}>
                  ID: {a.anomaly_id.slice(0, 18)}...
                </span>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Drill-down Anomaly Modal Drawer */}
      {selectedAnomaly && (
        <div className="fixed inset-0 z-50 bg-[#29272B]/60 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-[#FFFEFC] border border-[#DCD3C8] rounded-2xl w-full max-w-xl overflow-hidden shadow-2xl flex flex-col">
            <div className="px-6 py-4 border-b border-[#DCD3C8] bg-[#F8F5F0] flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Flame className="w-4 h-4 text-[#A74449]" />
                <h3 className="font-heading font-bold text-sm text-[#29272B]">
                  Isolation Forest Outlier Diagnostic
                </h3>
              </div>
              <button
                onClick={() => setSelectedAnomaly(null)}
                className="text-[#77716D] hover:text-[#29272B]"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="p-6 space-y-4 text-xs font-mono">
              <div className="grid grid-cols-2 gap-3 p-3 bg-[#F8F5F0] rounded-xl border border-[#DCD3C8]">
                <div>
                  <span className="text-[#77716D]">Device ID:</span>{' '}
                  <strong className="text-[#64283D]">{selectedAnomaly.device_id}</strong>
                </div>
                <div>
                  <span className="text-[#77716D]">Anomaly Score:</span>{' '}
                  <strong className="text-[#A74449]">{selectedAnomaly.anomaly_score.toFixed(4)}</strong>
                </div>
                <div>
                  <span className="text-[#77716D]">Model Confidence:</span>{' '}
                  <strong className="text-[#47745B]">{(selectedAnomaly.confidence * 100).toFixed(2)}%</strong>
                </div>
                <div>
                  <span className="text-[#77716D]">Primary Driver:</span>{' '}
                  <strong className="text-[#B08A59]">{selectedAnomaly.primary_driver}</strong>
                </div>
              </div>

              <div>
                <h4 className="font-sans font-bold text-[#29272B] mb-2">
                  Feature Standardized Deviations (σ-score):
                </h4>
                <div className="space-y-1.5 p-3 rounded-lg bg-[#29272B] border border-[#514850] text-[#EADDE2]">
                  {Object.entries(selectedAnomaly.feature_contributions || {}).map(([f, d]) => (
                    <div key={f} className="flex justify-between items-center py-0.5 border-b border-[#514850]/50 last:border-0">
                      <span>{f}</span>
                      <strong className={Number(d) > 10 ? 'text-[#A74449]' : 'text-[#B08A59]'}>
                        +{d}σ from nominal baseline
                      </strong>
                    </div>
                  ))}
                </div>
              </div>

              <div className="p-3 bg-[#F8F5F0] rounded-lg border border-[#DCD3C8] font-sans text-[#77716D] text-[11px]">
                <Info className="w-3.5 h-3.5 inline mr-1 text-[#B08A59]" />
                Events flagged as outliers remain in PostgreSQL for diagnostic forensics while passing through the fenced manifest ledger.
              </div>
            </div>

            <div className="px-6 py-3 border-t border-[#DCD3C8] bg-[#F8F5F0] flex justify-end">
              <button
                onClick={() => setSelectedAnomaly(null)}
                className="px-4 py-1.5 rounded-lg text-xs font-semibold bg-[#64283D] text-[#FFFEFC]"
              >
                Close Diagnostic
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
