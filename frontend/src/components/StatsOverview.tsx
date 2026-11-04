import React from 'react';
import { PipelineStats } from '../types';
import { CheckCircle2, AlertTriangle, Cpu, Flame, Layers } from 'lucide-react';

interface StatsProps {
  stats: PipelineStats | null;
}

export const StatsOverview: React.FC<StatsProps> = ({ stats }) => {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
      {/* 1. Valid Telemetry */}
      <div className="p-4 rounded-xl bg-[#FFFEFC] border border-[#DCD3C8] shadow-sm hover:border-[#B08A59] transition">
        <div className="flex items-center justify-between">
          <span className="text-xs font-medium text-[#77716D]">Valid Telemetry</span>
          <div className="p-1 rounded bg-[#47745B]/10 text-[#47745B]">
            <CheckCircle2 className="w-4 h-4" />
          </div>
        </div>
        <div className="mt-2 text-2xl font-bold text-[#29272B] font-mono">
          {stats?.valid_events_total?.toLocaleString() ?? '—'}
        </div>
        <div className="mt-1 flex items-center gap-1.5 text-[11px] text-[#47745B] font-medium font-sans">
          <span className="w-1.5 h-1.5 rounded-full bg-[#47745B]"></span>
          <span>PostgreSQL & MinIO S3a</span>
        </div>
      </div>

      {/* 2. Quarantined Rejects */}
      <div className="p-4 rounded-xl bg-[#FFFEFC] border border-[#DCD3C8] shadow-sm hover:border-[#B08A59] transition">
        <div className="flex items-center justify-between">
          <span className="text-xs font-medium text-[#77716D]">Quarantined Rejects</span>
          <div className="p-1 rounded bg-[#A87531]/10 text-[#A87531]">
            <AlertTriangle className="w-4 h-4" />
          </div>
        </div>
        <div className="mt-2 text-2xl font-bold text-[#29272B] font-mono">
          {stats?.invalid_events_total?.toLocaleString() ?? '—'}
        </div>
        <div className="mt-1 flex items-center gap-1.5 text-[11px] text-[#A87531] font-medium font-sans">
          <span className="w-1.5 h-1.5 rounded-full bg-[#A87531]"></span>
          <span>events_invalid DLQ table</span>
        </div>
      </div>

      {/* 3. AI Anomalies */}
      <div className="p-4 rounded-xl bg-[#FFFEFC] border border-[#DCD3C8] shadow-sm hover:border-[#B08A59] transition">
        <div className="flex items-center justify-between">
          <span className="text-xs font-medium text-[#77716D]">AI Anomalies</span>
          <div className="p-1 rounded bg-[#A74449]/10 text-[#A74449]">
            <Flame className="w-4 h-4" />
          </div>
        </div>
        <div className="mt-2 text-2xl font-bold text-[#29272B] font-mono">
          {stats?.anomalies_total?.toLocaleString() ?? '—'}
        </div>
        <div className="mt-1 flex items-center gap-1.5 text-[11px] text-[#A74449] font-medium font-sans">
          <span className="w-1.5 h-1.5 rounded-full bg-[#A74449]"></span>
          <span>Isolation Forest Detections</span>
        </div>
      </div>

      {/* 4. Active Devices */}
      <div className="p-4 rounded-xl bg-[#FFFEFC] border border-[#DCD3C8] shadow-sm hover:border-[#B08A59] transition">
        <div className="flex items-center justify-between">
          <span className="text-xs font-medium text-[#77716D]">Active Devices</span>
          <div className="p-1 rounded bg-[#B08A59]/10 text-[#B08A59]">
            <Cpu className="w-4 h-4" />
          </div>
        </div>
        <div className="mt-2 text-2xl font-bold text-[#29272B] font-mono">
          {stats?.active_devices_total?.toLocaleString() ?? '—'}
        </div>
        <div className="mt-1 flex items-center gap-1.5 text-[11px] text-[#B08A59] font-medium font-sans">
          <span className="w-1.5 h-1.5 rounded-full bg-[#B08A59]"></span>
          <span>Active IoT device streams</span>
        </div>
      </div>

      {/* 5. Completed Microbatches */}
      <div className="p-4 rounded-xl bg-[#FFFEFC] border border-[#DCD3C8] shadow-sm hover:border-[#B08A59] transition">
        <div className="flex items-center justify-between">
          <span className="text-xs font-medium text-[#77716D]">Completed Batches</span>
          <div className="p-1 rounded bg-[#52758B]/10 text-[#52758B]">
            <Layers className="w-4 h-4" />
          </div>
        </div>
        <div className="mt-2 text-2xl font-bold text-[#29272B] font-mono">
          {stats?.successful_microbatches?.toLocaleString() ?? '—'}
        </div>
        <div className="mt-1 flex items-center gap-1.5 text-[11px] text-[#52758B] font-medium font-sans">
          <span className="w-1.5 h-1.5 rounded-full bg-[#52758B]"></span>
          <span>Fenced manifest ledger</span>
        </div>
      </div>
    </div>
  );
};
