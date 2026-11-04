import React from 'react';
import { TelemetryEvent } from '../types';
import { MapPin, Activity } from 'lucide-react';

interface TelemetryTableProps {
  events: TelemetryEvent[];
}

export const TelemetryTable: React.FC<TelemetryTableProps> = ({ events }) => {
  return (
    <div className="rounded-xl border border-[#514850] bg-[#29272B] overflow-hidden shadow-md">
      <div className="px-5 py-3.5 border-b border-[#514850] bg-[#39343A] flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Activity className="w-4 h-4 text-[#B08A59]" />
          <h2 className="text-sm font-semibold text-[#FFFEFC] font-heading">
            Live Ingested Telemetry Feed
          </h2>
        </div>
        <span className="text-xs text-[#DCD3C8] font-mono">
          Showing {events.length} latest events
        </span>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs text-[#EADDE2]">
          <thead className="bg-[#29272B] text-[#DCD3C8] uppercase font-mono text-[10px] tracking-wider border-b border-[#514850]">
            <tr>
              <th className="px-4 py-3">Timestamp</th>
              <th className="px-4 py-3">Device / Facility</th>
              <th className="px-4 py-3">Location</th>
              <th className="px-4 py-3">Temp (°C)</th>
              <th className="px-4 py-3">Vibe (mm/s)</th>
              <th className="px-4 py-3">Press (bar)</th>
              <th className="px-4 py-3">Power (kW)</th>
              <th className="px-4 py-3">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[#514850]/60 font-mono">
            {events.length === 0 ? (
              <tr>
                <td colSpan={8} className="px-4 py-8 text-center text-[#77716D] font-sans">
                  No telemetry records found. Waiting for pipeline ingest...
                </td>
              </tr>
            ) : (
              events.map((ev) => (
                <tr key={ev.event_id} className="hover:bg-[#39343A]/70 transition">
                  <td className="px-4 py-2.5 text-[#DCD3C8]">
                    {new Date(ev.timestamp).toLocaleTimeString()}
                  </td>
                  <td className="px-4 py-2.5">
                    <span className="font-semibold text-[#B08A59]">{ev.device_id}</span>
                    <span className="text-[#77716D] text-[11px] ml-1.5 font-sans">({ev.facility_id})</span>
                  </td>
                  <td className="px-4 py-2.5 text-[#DCD3C8] flex items-center gap-1 font-sans">
                    <MapPin className="w-3 h-3 text-[#77716D]" />
                    <span>{ev.location}</span>
                  </td>
                  <td className="px-4 py-2.5">
                    <span className={ev.temperature > 85 ? 'text-[#A87531] font-bold' : 'text-[#FFFEFC]'}>
                      {ev.temperature.toFixed(1)}
                    </span>
                  </td>
                  <td className="px-4 py-2.5">
                    <span className={ev.vibration > 10 ? 'text-[#A74449] font-bold' : 'text-[#FFFEFC]'}>
                      {ev.vibration.toFixed(2)}
                    </span>
                  </td>
                  <td className="px-4 py-2.5 text-[#FFFEFC]">{ev.pressure.toFixed(1)}</td>
                  <td className="px-4 py-2.5 text-[#DCD3C8]">
                    {ev.power_consumption !== undefined ? ev.power_consumption.toFixed(1) : '—'}
                  </td>
                  <td className="px-4 py-2.5">
                    <span
                      className={`inline-block px-2.5 py-0.5 rounded text-[10px] font-bold tracking-wide ${
                        ev.status_code === 'OK'
                          ? 'bg-[#47745B]/20 text-[#47745B] border border-[#47745B]/40'
                          : ev.status_code === 'WARNING'
                          ? 'bg-[#A87531]/20 text-[#A87531] border border-[#A87531]/40'
                          : ev.status_code === 'CRITICAL'
                          ? 'bg-[#A74449]/20 text-[#A74449] border border-[#A74449]/40'
                          : 'bg-[#B08A59]/20 text-[#B08A59] border border-[#B08A59]/40'
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
  );
};
