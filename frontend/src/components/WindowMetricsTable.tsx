import React from 'react';
import { WindowMetric } from '../types';
import { Clock } from 'lucide-react';

interface WindowMetricsProps {
  metrics: WindowMetric[];
}

export const WindowMetricsTable: React.FC<WindowMetricsProps> = ({ metrics }) => {
  return (
    <div className="rounded-xl border border-[#514850] bg-[#29272B] overflow-hidden shadow-md">
      <div className="px-5 py-3.5 border-b border-[#514850] bg-[#39343A] flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Clock className="w-4 h-4 text-[#B08A59]" />
          <h2 className="text-sm font-semibold text-[#FFFEFC] font-heading">
            Tumbling Window Aggregations (Spark Structured Streaming)
          </h2>
        </div>
        <span className="text-xs text-[#DCD3C8] font-mono">
          {metrics.length} windows computed
        </span>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs text-[#EADDE2]">
          <thead className="bg-[#29272B] text-[#DCD3C8] uppercase font-mono text-[10px] tracking-wider border-b border-[#514850]">
            <tr>
              <th className="px-4 py-3">Window Range</th>
              <th className="px-4 py-3">Device / Type</th>
              <th className="px-4 py-3">Event Count</th>
              <th className="px-4 py-3">Avg / Max Temp (°C)</th>
              <th className="px-4 py-3">Avg / Max Vibe (mm/s)</th>
              <th className="px-4 py-3">Avg Press (bar)</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[#514850]/60 font-mono">
            {metrics.length === 0 ? (
              <tr>
                <td colSpan={6} className="px-4 py-8 text-center text-[#77716D] font-sans">
                  No windowed aggregations computed yet.
                </td>
              </tr>
            ) : (
              metrics.map((m) => (
                <tr key={`${m.window_start}-${m.device_id || m.device_type}`} className="hover:bg-[#39343A]/70 transition">
                  <td className="px-4 py-2.5 text-[#DCD3C8]">
                    {new Date(m.window_start).toLocaleTimeString()} – {new Date(m.window_end).toLocaleTimeString()}
                  </td>
                  <td className="px-4 py-2.5 font-semibold text-[#B08A59]">
                    {m.device_id || m.device_type}
                  </td>
                  <td className="px-4 py-2.5">
                    <span className="px-2 py-0.5 rounded bg-[#52758B]/20 text-[#52758B] font-bold border border-[#52758B]/40">
                      {m.event_count}
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
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};
