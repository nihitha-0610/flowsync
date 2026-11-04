import React, { useState } from 'react';
import {
  AlertTriangle,
  CheckCircle2,
  Copy,
  Database,
  Download,
  Filter,
  MapPin,
  Search,
  X,
} from 'lucide-react';
import { PageHeader } from '../components/PageHeader';
import { InvalidEvent, TelemetryEvent } from '../types';

interface ExplorerPageProps {
  events: TelemetryEvent[];
  invalidEvents: InvalidEvent[];
}

export const EventExplorerPage: React.FC<ExplorerPageProps> = ({
  events,
  invalidEvents,
}) => {
  const [activeTab, setActiveTab] = useState<'valid' | 'invalid'>('valid');
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('ALL');
  const [selectedEvent, setSelectedEvent] = useState<TelemetryEvent | InvalidEvent | null>(null);
  const [copied, setCopied] = useState(false);

  // Filter valid events
  const filteredValidEvents = events.filter((ev) => {
    const matchesSearch =
      ev.device_id.toLowerCase().includes(searchQuery.toLowerCase()) ||
      ev.facility_id.toLowerCase().includes(searchQuery.toLowerCase()) ||
      ev.location.toLowerCase().includes(searchQuery.toLowerCase()) ||
      ev.event_id.toLowerCase().includes(searchQuery.toLowerCase());

    const matchesStatus = statusFilter === 'ALL' || ev.status_code === statusFilter;
    return matchesSearch && matchesStatus;
  });

  // Filter invalid events
  const filteredInvalidEvents = invalidEvents.filter((ev) => {
    const rawStr = JSON.stringify(ev.raw_payload || '').toLowerCase();
    const matchesSearch =
      (ev.event_id && ev.event_id.toLowerCase().includes(searchQuery.toLowerCase())) ||
      (ev.failure_reason && ev.failure_reason.toLowerCase().includes(searchQuery.toLowerCase())) ||
      (ev.failed_field && ev.failed_field.toLowerCase().includes(searchQuery.toLowerCase())) ||
      rawStr.includes(searchQuery.toLowerCase());
    return matchesSearch;
  });

  const handleCopyJson = (obj: any) => {
    navigator.clipboard.writeText(JSON.stringify(obj, null, 2));
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleExportData = () => {
    const dataToExport = activeTab === 'valid' ? filteredValidEvents : filteredInvalidEvents;
    const blob = new Blob([JSON.stringify(dataToExport, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `flowsync_${activeTab}_events_${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="space-y-6">
      <PageHeader
        pageId="explorer"
        title="Event Stream Explorer & Dead Letter Queue"
        description="Deep-dive into individual industrial telemetry events. Inspect schema validation stages, partition offsets, calibrated sensor bounds, and quarantined parse failures."
        actions={
          <button
            onClick={handleExportData}
            className="flex items-center gap-1.5 px-3.5 py-2 rounded-lg text-xs font-medium bg-[#FFFEFC] hover:bg-[#E9DFD2] text-[#29272B] border border-[#DCD3C8] transition active:scale-95 shadow-2xs"
          >
            <Download className="w-3.5 h-3.5 text-[#B08A59]" />
            <span>Export JSON</span>
          </button>
        }
      />

      {/* Tabs & Search Filter Header */}
      <div className="p-4 rounded-xl bg-[#FFFEFC] border border-[#DCD3C8] shadow-xs flex flex-col md:flex-row md:items-center justify-between gap-4">
        {/* Valid / Invalid Stream Toggle Tabs */}
        <div className="flex items-center gap-1.5 p-1 bg-[#F8F5F0] rounded-lg border border-[#DCD3C8]">
          <button
            onClick={() => setActiveTab('valid')}
            className={`flex items-center gap-2 px-3.5 py-1.5 rounded-md text-xs font-semibold transition ${
              activeTab === 'valid'
                ? 'bg-[#64283D] text-[#FFFEFC] shadow-2xs'
                : 'text-[#77716D] hover:text-[#29272B]'
            }`}
          >
            <CheckCircle2 className="w-3.5 h-3.5" />
            <span>Valid Telemetry</span>
            <span className="ml-1 px-1.5 py-0.2 rounded-full text-[10px] font-mono bg-[#FFFEFC]/20">
              {events.length}
            </span>
          </button>

          <button
            onClick={() => setActiveTab('invalid')}
            className={`flex items-center gap-2 px-3.5 py-1.5 rounded-md text-xs font-semibold transition ${
              activeTab === 'invalid'
                ? 'bg-[#A87531] text-[#FFFEFC] shadow-2xs'
                : 'text-[#77716D] hover:text-[#29272B]'
            }`}
          >
            <AlertTriangle className="w-3.5 h-3.5" />
            <span>Quarantined DLQ</span>
            <span className="ml-1 px-1.5 py-0.2 rounded-full text-[10px] font-mono bg-[#FFFEFC]/20">
              {invalidEvents.length}
            </span>
          </button>
        </div>

        {/* Filter Controls */}
        <div className="flex flex-wrap items-center gap-3">
          {/* Search bar */}
          <div className="relative min-w-[240px]">
            <Search className="w-3.5 h-3.5 text-[#77716D] absolute left-3 top-2.5" />
            <input
              type="text"
              placeholder={
                activeTab === 'valid'
                  ? 'Search device, facility, location...'
                  : 'Search failure reason, field...'
              }
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-8 pr-3 py-1.5 rounded-lg text-xs bg-[#F8F5F0] border border-[#DCD3C8] text-[#29272B] focus:border-[#64283D] focus:outline-none font-mono"
            />
          </div>

          {/* Status filter (only for valid tab) */}
          {activeTab === 'valid' && (
            <div className="flex items-center gap-1.5 text-xs">
              <Filter className="w-3.5 h-3.5 text-[#77716D]" />
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="bg-[#F8F5F0] border border-[#DCD3C8] rounded-lg px-2.5 py-1.5 text-xs text-[#29272B] focus:outline-none focus:border-[#64283D]"
              >
                <option value="ALL">All Statuses</option>
                <option value="OK">OK</option>
                <option value="WARNING">WARNING</option>
                <option value="CRITICAL">CRITICAL</option>
                <option value="MAINTENANCE">MAINTENANCE</option>
              </select>
            </div>
          )}
        </div>
      </div>

      {/* Main Data Table */}
      <div className="rounded-xl border border-[#514850] bg-[#29272B] overflow-hidden shadow-md">
        <div className="overflow-x-auto">
          {activeTab === 'valid' ? (
            <table className="w-full text-left text-xs font-mono text-[#EADDE2]">
              <thead className="bg-[#39343A] text-[#DCD3C8] uppercase text-[10px] tracking-wider border-b border-[#514850]">
                <tr>
                  <th className="px-4 py-3">Timestamp</th>
                  <th className="px-4 py-3">Device / Facility</th>
                  <th className="px-4 py-3">Location</th>
                  <th className="px-4 py-3">Temp (°C)</th>
                  <th className="px-4 py-3">Vibe (mm/s)</th>
                  <th className="px-4 py-3">Press (bar)</th>
                  <th className="px-4 py-3">Flow (L/m)</th>
                  <th className="px-4 py-3">Power (kW)</th>
                  <th className="px-4 py-3">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#514850]/50">
                {filteredValidEvents.length === 0 ? (
                  <tr>
                    <td colSpan={9} className="px-4 py-10 text-center text-[#77716D] font-sans">
                      No matching valid events found.
                    </td>
                  </tr>
                ) : (
                  filteredValidEvents.map((ev) => (
                    <tr
                      key={ev.event_id}
                      onClick={() => setSelectedEvent(ev)}
                      className="hover:bg-[#39343A]/80 transition cursor-pointer"
                    >
                      <td className="px-4 py-2.5 text-[#DCD3C8]">
                        {new Date(ev.timestamp).toLocaleTimeString()}
                      </td>
                      <td className="px-4 py-2.5">
                        <span className="font-bold text-[#B08A59]">{ev.device_id}</span>
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
                        {ev.flow_rate !== undefined ? ev.flow_rate.toFixed(1) : '—'}
                      </td>
                      <td className="px-4 py-2.5 text-[#DCD3C8]">
                        {ev.power_consumption !== undefined ? ev.power_consumption.toFixed(1) : '—'}
                      </td>
                      <td className="px-4 py-2.5">
                        <span
                          className={`inline-block px-2.5 py-0.5 rounded text-[10px] font-bold ${
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
          ) : (
            <table className="w-full text-left text-xs font-mono text-[#EADDE2]">
              <thead className="bg-[#39343A] text-[#DCD3C8] uppercase text-[10px] tracking-wider border-b border-[#514850]">
                <tr>
                  <th className="px-4 py-3">Quarantined At</th>
                  <th className="px-4 py-3">Failure Stage</th>
                  <th className="px-4 py-3">Reason</th>
                  <th className="px-4 py-3">Failed Field</th>
                  <th className="px-4 py-3">Kafka Topic / Partition / Offset</th>
                  <th className="px-4 py-3">Observed Value Sample</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#514850]/50">
                {filteredInvalidEvents.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="px-4 py-10 text-center text-[#77716D] font-sans">
                      No quarantined dead-letter queue records found.
                    </td>
                  </tr>
                ) : (
                  filteredInvalidEvents.map((inv) => (
                    <tr
                      key={inv.id}
                      onClick={() => setSelectedEvent(inv)}
                      className="hover:bg-[#39343A]/80 transition cursor-pointer"
                    >
                      <td className="px-4 py-2.5 text-[#DCD3C8]">
                        {new Date(inv.quarantined_at).toLocaleTimeString()}
                      </td>
                      <td className="px-4 py-2.5">
                        <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-[#64283D]/40 text-[#EADDE2] border border-[#64283D]">
                          {inv.failure_stage || 'contract_check'}
                        </span>
                      </td>
                      <td className="px-4 py-2.5 text-[#A74449] font-bold">
                        {inv.failure_reason || 'schema_violation'}
                      </td>
                      <td className="px-4 py-2.5 text-[#B08A59] font-semibold">
                        {inv.failed_field || 'payload'}
                      </td>
                      <td className="px-4 py-2.5 text-[#DCD3C8]">
                        {inv.kafka_topic}:{inv.kafka_partition}:{inv.kafka_offset}
                      </td>
                      <td className="px-4 py-2.5 text-[#77716D] truncate max-w-xs" title={inv.observed_value}>
                        {inv.observed_value || inv.raw_text || '—'}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          )}
        </div>
      </div>

      {/* Inspector Modal Drawer */}
      {selectedEvent && (
        <div className="fixed inset-0 z-50 bg-[#29272B]/60 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-[#FFFEFC] border border-[#DCD3C8] rounded-2xl w-full max-w-2xl overflow-hidden shadow-2xl flex flex-col max-h-[85vh]">
            <div className="px-6 py-4 border-b border-[#DCD3C8] bg-[#F8F5F0] flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Database className="w-4 h-4 text-[#64283D]" />
                <h3 className="font-heading font-bold text-sm text-[#29272B]">
                  Event Record Inspector
                </h3>
              </div>
              <button
                onClick={() => setSelectedEvent(null)}
                className="text-[#77716D] hover:text-[#29272B]"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="p-6 overflow-y-auto space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-[#77716D]">JSON Serialization</span>
                <button
                  onClick={() => handleCopyJson(selectedEvent)}
                  className="flex items-center gap-1.5 px-2.5 py-1 text-xs font-medium rounded bg-[#F8F5F0] hover:bg-[#E9DFD2] border border-[#DCD3C8] text-[#29272B] transition"
                >
                  <Copy className="w-3.5 h-3.5 text-[#64283D]" />
                  <span>{copied ? 'Copied!' : 'Copy JSON'}</span>
                </button>
              </div>

              <pre className="p-4 rounded-xl bg-[#29272B] border border-[#514850] text-[#EADDE2] font-mono text-xs overflow-x-auto">
                {JSON.stringify(selectedEvent, null, 2)}
              </pre>
            </div>

            <div className="px-6 py-3 border-t border-[#DCD3C8] bg-[#F8F5F0] flex justify-end">
              <button
                onClick={() => setSelectedEvent(null)}
                className="px-4 py-1.5 rounded-lg text-xs font-semibold bg-[#64283D] text-[#FFFEFC]"
              >
                Close Inspector
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

