import React, { useState } from 'react';
import {
  Clock,
  LineChart,
  SlidersHorizontal,
} from 'lucide-react';
import { PageHeader } from '../components/PageHeader';
import { WindowMetric } from '../types';

interface AnalyticsPageProps {
  metrics: WindowMetric[];
}

export const StreamAnalyticsPage: React.FC<AnalyticsPageProps> = ({ metrics }) => {
  const [selectedDevice, setSelectedDevice] = useState<string>('ALL');

  const devices = Array.from(new Set(metrics.map((m) => m.device_id || m.device_type || 'Unknown')));

  const filteredMetrics = selectedDevice === 'ALL'
    ? metrics
    : metrics.filter((m) => (m.device_id || m.device_type) === selectedDevice);

  // Time-series chart points calculation
  const maxEvents = Math.max(...metrics.map((m) => m.event_count), 10);
  const maxTemp = Math.max(...metrics.map((m) => m.max_temperature || 0), 100);

  return (
    <div className="space-y-6">
      <PageHeader
        pageId="analytics"
        title="Structured Streaming 1-Minute Tumbling Windows"
        description="Near-real-time stateful aggregations maintained by Spark Structured Streaming Query B. State store snapshots compute sliding device metrics with strict event-time watermarking."
        actions={
          <div className="flex items-center gap-2">
            <SlidersHorizontal className="w-3.5 h-3.5 text-[#77716D]" />
            <select
              value={selectedDevice}
              onChange={(e) => setSelectedDevice(e.target.value)}
              className="bg-[#FFFEFC] border border-[#DCD3C8] rounded-lg px-3 py-1.5 text-xs text-[#29272B] focus:outline-none focus:border-[#64283D] font-mono shadow-2xs"
            >
              <option value="ALL">All Devices ({devices.length})</option>
              {devices.map((d) => (
                <option key={d} value={d}>{d}</option>
              ))}
            </select>
          </div>
        }
      />

      {/* 1. Analytics KPI Summaries */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="p-4 rounded-xl bg-[#FFFEFC] border border-[#DCD3C8] shadow-xs">
          <span className="text-xs font-medium text-[#77716D]">Computed Windows</span>
          <div className="mt-1.5 text-2xl font-bold font-mono text-[#29272B]">
            {metrics.length}
          </div>
          <span className="text-[11px] text-[#52758B]">1-Min Tumbling Duration</span>
        </div>

        <div className="p-4 rounded-xl bg-[#FFFEFC] border border-[#DCD3C8] shadow-xs">
          <span className="text-xs font-medium text-[#77716D]">Max Batch Density</span>
          <div className="mt-1.5 text-2xl font-bold font-mono text-[#47745B]">
            {Math.max(...metrics.map((m) => m.event_count), 0)}
          </div>
          <span className="text-[11px] text-[#77716D]">Events / Window</span>
        </div>

        <div className="p-4 rounded-xl bg-[#FFFEFC] border border-[#DCD3C8] shadow-xs">
          <span className="text-xs font-medium text-[#77716D]">Peak Window Temp</span>
          <div className="mt-1.5 text-2xl font-bold font-mono text-[#A87531]">
            {Math.max(...metrics.map((m) => m.max_temperature || 0), 0).toFixed(1)}°C
          </div>
          <span className="text-[11px] text-[#77716D]">Aggregated Maximum</span>
        </div>

        <div className="p-4 rounded-xl bg-[#FFFEFC] border border-[#DCD3C8] shadow-xs">
          <span className="text-xs font-medium text-[#77716D]">Peak Window Vibration</span>
          <div className="mt-1.5 text-2xl font-bold font-mono text-[#A74449]">
            {Math.max(...metrics.map((m) => m.max_vibration || 0), 0).toFixed(2)}
          </div>
          <span className="text-[11px] text-[#77716D]">mm/s RMS Maximum</span>
        </div>
      </div>

      {/* 2. Visual Time-Series Trends (SVG Chart) */}
      <div className="p-6 rounded-xl bg-[#FFFEFC] border border-[#DCD3C8] shadow-xs">
        <div className="flex items-center justify-between pb-4 mb-4 border-b border-[#DCD3C8]">
          <div className="flex items-center gap-2">
            <LineChart className="w-4 h-4 text-[#64283D]" />
            <h3 className="font-heading font-bold text-sm text-[#29272B]">
              Window Density & Temperature Distribution
            </h3>
          </div>
          <div className="flex items-center gap-4 text-xs font-mono">
            <div className="flex items-center gap-1.5">
              <span className="w-3 h-3 rounded bg-[#64283D]/20 border border-[#64283D]"></span>
              <span className="text-[#77716D]">Events Count</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="w-3 h-1 rounded bg-[#B08A59]"></span>
              <span className="text-[#77716D]">Max Temp (°C)</span>
            </div>
          </div>
        </div>

        {/* Responsive Bar / Trend Visualization */}
        {filteredMetrics.length === 0 ? (
          <div className="py-12 text-center text-[#77716D] text-xs font-sans">
            No windowed records found for selected filter.
          </div>
        ) : (
          <div className="space-y-4">
            <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-3">
              {filteredMetrics.map((m, idx) => {
                const countPct = Math.round((m.event_count / maxEvents) * 100);
                const tempPct = Math.round(((m.max_temperature || 0) / maxTemp) * 100);
                const startTime = new Date(m.window_start).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });

                return (
                  <div
                    key={`${m.window_start}-${m.device_id || idx}`}
                    className="p-3 rounded-lg bg-[#F8F5F0] border border-[#DCD3C8] flex flex-col justify-between"
                  >
                    <div>
                      <div className="flex items-center justify-between text-[11px] font-mono mb-1">
                        <span className="font-bold text-[#64283D] truncate max-w-[80px]">
                          {m.device_id || m.device_type}
                        </span>
                        <span className="text-[#77716D] text-[10px]">{startTime}</span>
                      </div>

                      {/* Mini Bar Graphs for Event Volume & Max Temp */}
                      <div className="w-full bg-[#DCD3C8] h-1.5 rounded-full overflow-hidden mt-2 mb-1">
                        <div
                          className="bg-[#64283D] h-full transition-all duration-500"
                          style={{ width: `${Math.min(countPct, 100)}%` }}
                          title={`Volume: ${m.event_count} events`}
                        />
                      </div>
                      <div className="w-full bg-[#DCD3C8] h-1.5 rounded-full overflow-hidden mb-2">
                        <div
                          className="bg-[#B08A59] h-full transition-all duration-500"
                          style={{ width: `${Math.min(tempPct, 100)}%` }}
                          title={`Peak Temperature: ${m.max_temperature?.toFixed(1)}°C`}
                        />
                      </div>
                    </div>

                    <div className="flex items-center justify-between text-[11px] font-mono mt-1 pt-1 border-t border-[#DCD3C8]">
                      <span className="text-[#77716D]">{m.event_count} evs</span>
                      <span className="font-bold text-[#B08A59]">
                        {m.max_temperature?.toFixed(1) ?? '—'}°C
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </div>

      {/* 3. Detailed Tumbling Windows Data Table */}
      <div className="rounded-xl border border-[#514850] bg-[#29272B] overflow-hidden shadow-md">
        <div className="px-5 py-3.5 border-b border-[#514850] bg-[#39343A] flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Clock className="w-4 h-4 text-[#B08A59]" />
            <h2 className="text-sm font-semibold text-[#FFFEFC] font-heading">
              Persisted Window Aggregation Ledger (PostgreSQL)
            </h2>
          </div>
          <span className="text-xs text-[#DCD3C8] font-mono">
            {filteredMetrics.length} windows in view
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs font-mono text-[#EADDE2]">
            <thead className="bg-[#29272B] text-[#DCD3C8] uppercase text-[10px] tracking-wider border-b border-[#514850]">
              <tr>
                <th className="px-4 py-3">Window Interval (UTC)</th>
                <th className="px-4 py-3">Device / Type</th>
                <th className="px-4 py-3">Event Volume</th>
                <th className="px-4 py-3">Avg / Max Temp (°C)</th>
                <th className="px-4 py-3">Avg / Max Vibe (mm/s)</th>
                <th className="px-4 py-3">Avg Press (bar)</th>
                <th className="px-4 py-3">Watermark State</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#514850]/50">
              {filteredMetrics.length === 0 ? (
                <tr>
                  <td colSpan={7} className="px-4 py-8 text-center text-[#77716D] font-sans">
                    No window aggregations recorded.
                  </td>
                </tr>
              ) : (
                filteredMetrics.map((m) => (
                  <tr key={`${m.window_start}-${m.device_id || m.device_type}`} className="hover:bg-[#39343A]/70 transition">
                    <td className="px-4 py-2.5 text-[#DCD3C8]">
                      {new Date(m.window_start).toLocaleTimeString()} – {new Date(m.window_end).toLocaleTimeString()}
                    </td>
                    <td className="px-4 py-2.5 font-bold text-[#B08A59]">
                      {m.device_id || m.device_type}
                    </td>
                    <td className="px-4 py-2.5">
                      <span className="px-2 py-0.5 rounded bg-[#52758B]/20 text-[#52758B] font-bold border border-[#52758B]/40">
                        {m.event_count} events
                      </span>
                    </td>
                    <td className="px-4 py-2.5">
                      <span className="text-[#FFFEFC]">{m.avg_temperature?.toFixed(1) ?? '—'}</span>
                      <span className="text-[#77716D] mx-1">/</span>
                      <span className="text-[#A87531] font-bold">{m.max_temperature?.toFixed(1) ?? '—'}</span>
                    </td>
                    <td className="px-4 py-2.5">
                      <span className="text-[#FFFEFC]">{m.avg_vibration?.toFixed(2) ?? '—'}</span>
                      <span className="text-[#77716D] mx-1">/</span>
                      <span className="text-[#A74449] font-bold">{m.max_vibration?.toFixed(2) ?? '—'}</span>
                    </td>
                    <td className="px-4 py-2.5 text-[#FFFEFC]">
                      {m.avg_pressure?.toFixed(1) ?? '—'}
                    </td>
                    <td className="px-4 py-2.5">
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-[#47745B]/20 text-[#47745B] border border-[#47745B]/40">
                        COMMITTED
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
