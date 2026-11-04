import React, { useState } from 'react';
import {
  AlertTriangle,
  CheckCircle2,
  Cpu,
  Info,
  Send,
  ShieldCheck,
  Sparkles,
  Zap,
} from 'lucide-react';
import { PageHeader } from '../components/PageHeader';
import { ingestManualEvent } from '../services/api';
import { TelemetryEvent } from '../types';

interface IngestionPageProps {
  onEventIngested: () => void;
  recentEvents: TelemetryEvent[];
}

export const DataIngestionPage: React.FC<IngestionPageProps> = ({
  onEventIngested,
  recentEvents,
}) => {
  const [deviceId, setDeviceId] = useState('DEV-0001');
  const [facilityId, setFacilityId] = useState('FAC-01');
  const [location, setLocation] = useState('Turbine-Hall-A');
  const [temperature, setTemperature] = useState(65.0);
  const [vibration, setVibration] = useState(3.5);
  const [pressure, setPressure] = useState(42.0);
  const [flowRate, setFlowRate] = useState(240.0);
  const [power, setPower] = useState(45.0);
  const [status, setStatus] = useState<'OK' | 'WARNING' | 'CRITICAL' | 'MAINTENANCE'>('OK');

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [feedback, setFeedback] = useState<{
    type: 'success' | 'error';
    title: string;
    message: string;
    timestamp: string;
  } | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    setFeedback(null);

    const payload = {
      device_id: deviceId.trim(),
      facility_id: facilityId.trim(),
      location: location.trim(),
      timestamp: new Date().toISOString().replace(/\.\d{3}/, ''),
      temperature: Number(temperature),
      vibration: Number(vibration),
      pressure: Number(pressure),
      flow_rate: Number(flowRate),
      power_consumption: Number(power),
      status_code: status,
    };

    try {
      const res = await ingestManualEvent(payload);
      if (res.status === 'success' || res.published_count > 0) {
        setFeedback({
          type: 'success',
          title: 'Event Successfully Published to Kafka',
          message: `Published ${res.published_count} record to topic events.raw. Spark Structured Streaming is processing the micro-batch.`,
          timestamp: new Date().toLocaleTimeString(),
        });
        onEventIngested();
      } else {
        const errorDetail = res.errors?.[0]?.error || 'Unknown ingestion contract failure';
        setFeedback({
          type: 'error',
          title: 'Contract Validation Rejection',
          message: errorDetail,
          timestamp: new Date().toLocaleTimeString(),
        });
      }
    } catch (err: any) {
      setFeedback({
        type: 'error',
        title: 'Network / Ingest Error',
        message: err.message,
        timestamp: new Date().toLocaleTimeString(),
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleApplyPreset = (preset: 'nominal' | 'vibe_spike' | 'thermal_runaway' | 'maintenance') => {
    if (preset === 'nominal') {
      setDeviceId('DEV-0001');
      setFacilityId('FAC-01');
      setLocation('Turbine-Hall-A');
      setTemperature(65.0);
      setVibration(3.2);
      setPressure(42.0);
      setFlowRate(240.0);
      setPower(45.0);
      setStatus('OK');
    } else if (preset === 'vibe_spike') {
      setDeviceId('DEV-0005');
      setFacilityId('FAC-01');
      setLocation('Vibration-Test-Unit');
      setTemperature(78.5);
      setVibration(14.8); // High vibration spike
      setPressure(45.0);
      setFlowRate(250.0);
      setPower(52.0);
      setStatus('WARNING');
    } else if (preset === 'thermal_runaway') {
      setDeviceId('DEV-0002');
      setFacilityId('FAC-02');
      setLocation('Primary-Generator-Vault');
      setTemperature(118.0); // Severe temperature
      setVibration(8.5);
      setPressure(85.0);
      setFlowRate(420.0);
      setPower(88.0);
      setStatus('CRITICAL');
    } else if (preset === 'maintenance') {
      setDeviceId('DEV-0003');
      setFacilityId('FAC-01');
      setLocation('Aux-Pump-Station');
      setTemperature(42.0);
      setVibration(1.1);
      setPressure(22.0);
      setFlowRate(95.0);
      setPower(12.0);
      setStatus('MAINTENANCE');
    }
  };

  return (
    <div className="space-y-6">
      <PageHeader
        pageId="ingestion"
        title="Industrial Telemetry Ingestion Hub"
        description="Produce live sensor telemetry into the Kafka events.raw topic. Supports strict canonical contract validation (DEV-XXXX, FAC-XX), manual overrides, and real-time anomaly simulation."
      />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Form & Presets (2 cols) */}
        <div className="lg:col-span-2 space-y-6">
          {/* Quick Simulation Presets */}
          <div className="p-4 rounded-xl bg-[#FFFEFC] border border-[#DCD3C8] shadow-xs flex flex-wrap items-center justify-between gap-3">
            <div className="flex items-center gap-2 text-xs font-semibold text-[#29272B]">
              <Sparkles className="w-4 h-4 text-[#B08A59]" />
              <span>Simulation Presets:</span>
            </div>
            <div className="flex flex-wrap items-center gap-2">
              <button
                type="button"
                onClick={() => handleApplyPreset('nominal')}
                className="px-3 py-1.5 rounded-lg text-xs font-medium bg-[#F8F5F0] hover:bg-[#E9DFD2] border border-[#DCD3C8] text-[#47745B] transition active:scale-95"
              >
                Nominal Operation
              </button>
              <button
                type="button"
                onClick={() => handleApplyPreset('vibe_spike')}
                className="px-3 py-1.5 rounded-lg text-xs font-medium bg-[#A74449]/10 hover:bg-[#A74449]/20 border border-[#A74449]/30 text-[#A74449] transition active:scale-95"
              >
                Vibration Outlier Spike
              </button>
              <button
                type="button"
                onClick={() => handleApplyPreset('thermal_runaway')}
                className="px-3 py-1.5 rounded-lg text-xs font-medium bg-[#A87531]/10 hover:bg-[#A87531]/20 border border-[#A87531]/30 text-[#A87531] transition active:scale-95"
              >
                Thermal Runaway
              </button>
              <button
                type="button"
                onClick={() => handleApplyPreset('maintenance')}
                className="px-3 py-1.5 rounded-lg text-xs font-medium bg-[#52758B]/10 hover:bg-[#52758B]/20 border border-[#52758B]/30 text-[#52758B] transition active:scale-95"
              >
                Scheduled Maintenance
              </button>
            </div>
          </div>

          {/* Ingestion Form Card */}
          <div className="p-6 rounded-xl bg-[#FFFEFC] border border-[#DCD3C8] shadow-xs">
            <form onSubmit={handleSubmit} className="space-y-5">
              {/* Device and Facility Group */}
              <div>
                <h3 className="font-heading font-bold text-sm text-[#64283D] pb-2 border-b border-[#DCD3C8] flex items-center gap-2">
                  <Cpu className="w-4 h-4 text-[#B08A59]" />
                  <span>1. Device & Facility Identification</span>
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-3 text-xs">
                  <div>
                    <label className="block text-[#77716D] font-medium mb-1 font-sans">
                      Device ID <span className="text-[#A74449] font-mono">* (DEV-XXXX)</span>
                    </label>
                    <input
                      type="text"
                      pattern="^DEV-[0-9]{4}$"
                      title="Must match pattern DEV-0001 to DEV-9999"
                      value={deviceId}
                      onChange={(e) => setDeviceId(e.target.value)}
                      className="w-full bg-[#F8F5F0] border border-[#DCD3C8] rounded-lg px-3 py-2 font-mono text-[#29272B] focus:border-[#64283D] focus:outline-none"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-[#77716D] font-medium mb-1 font-sans">
                      Facility ID <span className="text-[#A74449] font-mono">* (FAC-XX)</span>
                    </label>
                    <input
                      type="text"
                      pattern="^FAC-[0-9]{2}$"
                      title="Must match pattern FAC-01 to FAC-99"
                      value={facilityId}
                      onChange={(e) => setFacilityId(e.target.value)}
                      className="w-full bg-[#F8F5F0] border border-[#DCD3C8] rounded-lg px-3 py-2 font-mono text-[#29272B] focus:border-[#64283D] focus:outline-none"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-[#77716D] font-medium mb-1 font-sans">
                      Location / Hall <span className="text-[#A74449] font-mono">*</span>
                    </label>
                    <input
                      type="text"
                      value={location}
                      onChange={(e) => setLocation(e.target.value)}
                      className="w-full bg-[#F8F5F0] border border-[#DCD3C8] rounded-lg px-3 py-2 font-mono text-[#29272B] focus:border-[#64283D] focus:outline-none"
                      required
                    />
                  </div>
                </div>
              </div>

              {/* Physical Sensor Measurements Group */}
              <div>
                <h3 className="font-heading font-bold text-sm text-[#64283D] pb-2 border-b border-[#DCD3C8] flex items-center gap-2">
                  <Zap className="w-4 h-4 text-[#B08A59]" />
                  <span>2. Calibrated Sensor Telemetry</span>
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-3 text-xs">
                  <div>
                    <label className="block text-[#77716D] font-medium mb-1 font-sans">
                      Temperature (°C) <span className="text-[#77716D] font-mono">[-40 to 125]</span>
                    </label>
                    <input
                      type="number"
                      step="0.1"
                      min="-40"
                      max="125"
                      value={temperature}
                      onChange={(e) => setTemperature(parseFloat(e.target.value))}
                      className="w-full bg-[#F8F5F0] border border-[#DCD3C8] rounded-lg px-3 py-2 font-mono text-[#29272B] focus:border-[#64283D] focus:outline-none"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-[#77716D] font-medium mb-1 font-sans">
                      Vibration (mm/s) <span className="text-[#77716D] font-mono">[0 to 15]</span>
                    </label>
                    <input
                      type="number"
                      step="0.05"
                      min="0"
                      max="15"
                      value={vibration}
                      onChange={(e) => setVibration(parseFloat(e.target.value))}
                      className="w-full bg-[#F8F5F0] border border-[#DCD3C8] rounded-lg px-3 py-2 font-mono text-[#29272B] focus:border-[#64283D] focus:outline-none"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-[#77716D] font-medium mb-1 font-sans">
                      Pressure (bar) <span className="text-[#77716D] font-mono">[0 to 100]</span>
                    </label>
                    <input
                      type="number"
                      step="0.1"
                      min="0"
                      max="100"
                      value={pressure}
                      onChange={(e) => setPressure(parseFloat(e.target.value))}
                      className="w-full bg-[#F8F5F0] border border-[#DCD3C8] rounded-lg px-3 py-2 font-mono text-[#29272B] focus:border-[#64283D] focus:outline-none"
                      required
                    />
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-3 text-xs">
                  <div>
                    <label className="block text-[#77716D] font-medium mb-1 font-sans">
                      Flow Rate (L/min) <span className="text-[#77716D] font-mono">[0 to 500]</span>
                    </label>
                    <input
                      type="number"
                      step="1"
                      min="0"
                      max="500"
                      value={flowRate}
                      onChange={(e) => setFlowRate(parseFloat(e.target.value))}
                      className="w-full bg-[#F8F5F0] border border-[#DCD3C8] rounded-lg px-3 py-2 font-mono text-[#29272B] focus:border-[#64283D] focus:outline-none"
                    />
                  </div>
                  <div>
                    <label className="block text-[#77716D] font-medium mb-1 font-sans">
                      Power Consumption (kW) <span className="text-[#77716D] font-mono">[0 to 100]</span>
                    </label>
                    <input
                      type="number"
                      step="0.5"
                      min="0"
                      max="100"
                      value={power}
                      onChange={(e) => setPower(parseFloat(e.target.value))}
                      className="w-full bg-[#F8F5F0] border border-[#DCD3C8] rounded-lg px-3 py-2 font-mono text-[#29272B] focus:border-[#64283D] focus:outline-none"
                    />
                  </div>
                  <div>
                    <label className="block text-[#77716D] font-medium mb-1 font-sans">
                      Operational Status Code <span className="text-[#A74449] font-mono">*</span>
                    </label>
                    <select
                      value={status}
                      onChange={(e: any) => setStatus(e.target.value)}
                      className="w-full bg-[#F8F5F0] border border-[#DCD3C8] rounded-lg px-3 py-2 font-mono text-[#29272B] focus:border-[#64283D] focus:outline-none"
                    >
                      <option value="OK">OK — Nominal Status</option>
                      <option value="WARNING">WARNING — Operational Warning</option>
                      <option value="CRITICAL">CRITICAL — Plant Emergency</option>
                      <option value="MAINTENANCE">MAINTENANCE — Field Servicing</option>
                    </select>
                  </div>
                </div>
              </div>

              {/* Submit CTA */}
              <div className="pt-3 flex items-center justify-between border-t border-[#DCD3C8]">
                <div className="flex items-center gap-2 text-xs text-[#77716D]">
                  <Info className="w-3.5 h-3.5 text-[#B08A59]" />
                  <span>Payload is signed with ISO-8601 UTC timestamp upon submission.</span>
                </div>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="flex items-center gap-2 px-6 py-2.5 rounded-lg text-xs font-semibold bg-[#64283D] hover:bg-[#4A1D2E] text-[#FFFEFC] transition active:scale-95 shadow-sm"
                >
                  <Send className={`w-3.5 h-3.5 text-[#B08A59] ${isSubmitting ? 'animate-bounce' : ''}`} />
                  <span>{isSubmitting ? 'Publishing to Kafka...' : 'Publish Telemetry to Kafka'}</span>
                </button>
              </div>
            </form>
          </div>

          {/* Feedback Banner */}
          {feedback && (
            <div
              className={`p-4 rounded-xl border flex items-start gap-3 text-xs ${
                feedback.type === 'success'
                  ? 'bg-[#47745B]/10 border-[#47745B]/30 text-[#47745B]'
                  : 'bg-[#A74449]/10 border-[#A74449]/30 text-[#A74449]'
              }`}
            >
              {feedback.type === 'success' ? (
                <CheckCircle2 className="w-5 h-5 shrink-0 text-[#47745B]" />
              ) : (
                <AlertTriangle className="w-5 h-5 shrink-0 text-[#A74449]" />
              )}
              <div className="flex-1">
                <div className="flex items-center justify-between">
                  <h4 className="font-bold font-sans">{feedback.title}</h4>
                  <span className="font-mono text-[10px] text-[#77716D]">{feedback.timestamp}</span>
                </div>
                <p className="mt-1 font-mono text-[11px] leading-relaxed break-all">
                  {feedback.message}
                </p>
              </div>
            </div>
          )}
        </div>

        {/* Right Column: Ingestion Log & Canonical Contract Docs */}
        <div className="space-y-6">
          {/* Canonical Contract Reference */}
          <div className="p-5 rounded-xl bg-[#FFFEFC] border border-[#DCD3C8] shadow-xs">
            <h3 className="font-heading font-bold text-sm text-[#29272B] mb-2 flex items-center gap-2">
              <ShieldCheck className="w-4 h-4 text-[#47745B]" />
              <span>Canonical Ingestion Contract</span>
            </h3>
            <p className="text-xs text-[#77716D] mb-3 font-sans">
              Layer B contract invariants enforced by Spark Structured Streaming:
            </p>
            <div className="space-y-1.5 font-mono text-[11px] text-[#29272B]">
              <div className="flex justify-between py-1 border-b border-[#DCD3C8]/50">
                <span className="text-[#77716D]">device_id</span>
                <span className="text-[#64283D] font-semibold">DEV-[0-9]{4}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-[#DCD3C8]/50">
                <span className="text-[#77716D]">facility_id</span>
                <span className="text-[#64283D] font-semibold">FAC-[0-9]{2}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-[#DCD3C8]/50">
                <span className="text-[#77716D]">temperature</span>
                <span>-40.0 to 125.0 °C</span>
              </div>
              <div className="flex justify-between py-1 border-b border-[#DCD3C8]/50">
                <span className="text-[#77716D]">vibration</span>
                <span>0.0 to 15.0 mm/s</span>
              </div>
              <div className="flex justify-between py-1 border-b border-[#DCD3C8]/50">
                <span className="text-[#77716D]">pressure</span>
                <span>0.0 to 100.0 bar</span>
              </div>
              <div className="flex justify-between py-1 border-b border-[#DCD3C8]/50">
                <span className="text-[#77716D]">flow_rate</span>
                <span>0.0 to 500.0 L/min</span>
              </div>
              <div className="flex justify-between py-1 border-b border-[#DCD3C8]/50">
                <span className="text-[#77716D]">power</span>
                <span>0.0 to 100.0 kW</span>
              </div>
              <div className="flex justify-between py-1">
                <span className="text-[#77716D]">status_code</span>
                <span className="text-[#B08A59] font-semibold">OK | WARN | CRIT | MAINT</span>
              </div>
            </div>
          </div>

          {/* Recent Ingestion Stream Card */}
          <div className="p-5 rounded-xl bg-[#29272B] border border-[#514850] shadow-md">
            <div className="flex items-center justify-between pb-3 mb-3 border-b border-[#514850]">
              <h3 className="font-heading font-bold text-xs text-[#FFFEFC]">
                Recent Ingested Activity
              </h3>
              <span className="text-[10px] font-mono text-[#DCD3C8]">
                {recentEvents.length} records
              </span>
            </div>

            <div className="space-y-2 max-h-[300px] overflow-y-auto font-mono text-xs">
              {recentEvents.slice(0, 8).map((ev) => (
                <div
                  key={ev.event_id}
                  className="p-2.5 rounded bg-[#39343A] border border-[#514850] flex items-center justify-between"
                >
                  <div>
                    <span className="font-bold text-[#B08A59]">{ev.device_id}</span>
                    <span className="text-[#DCD3C8] ml-2">{ev.temperature.toFixed(1)}°C</span>
                    <span className="text-[#77716D] ml-1">/</span>
                    <span className="text-[#DCD3C8] ml-1">{ev.vibration.toFixed(2)} mm/s</span>
                  </div>
                  <span
                    className={`px-1.5 py-0.2 rounded text-[10px] font-bold ${
                      ev.status_code === 'OK'
                        ? 'bg-[#47745B]/20 text-[#47745B]'
                        : 'bg-[#A87531]/20 text-[#A87531]'
                    }`}
                  >
                    {ev.status_code}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
