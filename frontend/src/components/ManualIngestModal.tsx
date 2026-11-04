import React, { useState } from 'react';
import { X, Send, Sparkles } from 'lucide-react';
import { ingestManualEvent } from '../services/api';

interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

export const ManualIngestModal: React.FC<ModalProps> = ({ isOpen, onClose, onSuccess }) => {
  const [deviceId, setDeviceId] = useState('DEV-0001');
  const [facilityId, setFacilityId] = useState('FAC-01');
  const [location, setLocation] = useState('Turbine-Hall-A');
  const [temperature, setTemperature] = useState(65.0);
  const [vibration, setVibration] = useState(4.2);
  const [pressure, setPressure] = useState(45.0);
  const [flowRate, setFlowRate] = useState(250.0);
  const [power, setPower] = useState(45.0);
  const [status, setStatus] = useState<'OK' | 'WARNING' | 'CRITICAL' | 'MAINTENANCE'>('OK');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    setMessage(null);

    const payload = {
      device_id: deviceId,
      facility_id: facilityId,
      location: location,
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
      setMessage(`Successfully published ${res.published_count} event to Kafka!`);
      setTimeout(() => {
        onSuccess();
        onClose();
      }, 1000);
    } catch (err: any) {
      setMessage(`Error: ${err.message}`);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleInjectAnomaly = () => {
    setVibration(14.8); // High vibration spike trigger
    setStatus('WARNING');
  };

  return (
    <div className="fixed inset-0 z-50 bg-[#29272B]/60 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-[#FFFEFC] border border-[#DCD3C8] rounded-2xl w-full max-w-lg overflow-hidden shadow-2xl animate-in fade-in zoom-in-95 duration-150">
        <div className="px-6 py-4 border-b border-[#DCD3C8] bg-[#F8F5F0] flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="p-1.5 rounded-lg bg-[#64283D] text-[#FFFEFC]">
              <Send className="w-4 h-4 text-[#B08A59]" />
            </div>
            <h3 className="text-sm font-bold text-[#64283D] font-heading">
              Ingest Telemetry Event
            </h3>
          </div>
          <button onClick={onClose} className="text-[#77716D] hover:text-[#29272B] transition">
            <X className="w-5 h-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <div className="grid grid-cols-2 gap-3 text-xs">
            <div>
              <label className="text-[#77716D] font-medium font-sans">Device ID</label>
              <input
                type="text"
                value={deviceId}
                onChange={(e) => setDeviceId(e.target.value)}
                className="mt-1 w-full bg-[#F8F5F0] border border-[#DCD3C8] rounded-lg px-3 py-2 text-[#29272B] font-mono focus:outline-none focus:border-[#64283D]"
                required
              />
            </div>
            <div>
              <label className="text-[#77716D] font-medium font-sans">Facility ID</label>
              <input
                type="text"
                value={facilityId}
                onChange={(e) => setFacilityId(e.target.value)}
                className="mt-1 w-full bg-[#F8F5F0] border border-[#DCD3C8] rounded-lg px-3 py-2 text-[#29272B] font-mono focus:outline-none focus:border-[#64283D]"
                required
              />
            </div>
          </div>

          <div className="text-xs">
            <label className="text-[#77716D] font-medium font-sans">Location</label>
            <input
              type="text"
              value={location}
              onChange={(e) => setLocation(e.target.value)}
              className="mt-1 w-full bg-[#F8F5F0] border border-[#DCD3C8] rounded-lg px-3 py-2 text-[#29272B] font-mono focus:outline-none focus:border-[#64283D]"
              required
            />
          </div>

          <div className="grid grid-cols-3 gap-3 text-xs">
            <div>
              <label className="text-[#77716D] font-medium font-sans">Temp (°C)</label>
              <input
                type="number"
                step="0.1"
                value={temperature}
                onChange={(e) => setTemperature(parseFloat(e.target.value))}
                className="mt-1 w-full bg-[#F8F5F0] border border-[#DCD3C8] rounded-lg px-3 py-2 text-[#29272B] font-mono focus:outline-none focus:border-[#64283D]"
              />
            </div>
            <div>
              <label className="text-[#77716D] font-medium font-sans">Vibe (mm/s)</label>
              <input
                type="number"
                step="0.05"
                value={vibration}
                onChange={(e) => setVibration(parseFloat(e.target.value))}
                className="mt-1 w-full bg-[#F8F5F0] border border-[#DCD3C8] rounded-lg px-3 py-2 text-[#29272B] font-mono focus:outline-none focus:border-[#64283D]"
              />
            </div>
            <div>
              <label className="text-[#77716D] font-medium font-sans">Press (bar)</label>
              <input
                type="number"
                step="0.1"
                value={pressure}
                onChange={(e) => setPressure(parseFloat(e.target.value))}
                className="mt-1 w-full bg-[#F8F5F0] border border-[#DCD3C8] rounded-lg px-3 py-2 text-[#29272B] font-mono focus:outline-none focus:border-[#64283D]"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3 text-xs">
            <div>
              <label className="text-[#77716D] font-medium font-sans">Flow Rate (L/min)</label>
              <input
                type="number"
                step="1"
                value={flowRate}
                onChange={(e) => setFlowRate(parseFloat(e.target.value))}
                className="mt-1 w-full bg-[#F8F5F0] border border-[#DCD3C8] rounded-lg px-3 py-2 text-[#29272B] font-mono focus:outline-none focus:border-[#64283D]"
              />
            </div>
            <div>
              <label className="text-[#77716D] font-medium font-sans">Power (kW)</label>
              <input
                type="number"
                step="0.5"
                value={power}
                onChange={(e) => setPower(parseFloat(e.target.value))}
                className="mt-1 w-full bg-[#F8F5F0] border border-[#DCD3C8] rounded-lg px-3 py-2 text-[#29272B] font-mono focus:outline-none focus:border-[#64283D]"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3 text-xs">
            <div>
              <label className="text-[#77716D] font-medium font-sans">Status Code</label>
              <select
                value={status}
                onChange={(e: any) => setStatus(e.target.value)}
                className="mt-1 w-full bg-[#F8F5F0] border border-[#DCD3C8] rounded-lg px-3 py-2 text-[#29272B] font-mono focus:outline-none focus:border-[#64283D]"
              >
                <option value="OK">OK</option>
                <option value="WARNING">WARNING</option>
                <option value="CRITICAL">CRITICAL</option>
                <option value="MAINTENANCE">MAINTENANCE</option>
              </select>
            </div>
            <div className="flex items-end">
              <button
                type="button"
                onClick={handleInjectAnomaly}
                className="w-full flex items-center justify-center gap-1.5 px-3 py-2 rounded-lg bg-[#A74449]/10 text-[#A74449] border border-[#A74449]/30 text-xs font-semibold hover:bg-[#A74449]/20 transition"
              >
                <Sparkles className="w-3.5 h-3.5" />
                <span>Simulate Anomaly</span>
              </button>
            </div>
          </div>

          {message && (
            <div className="p-3 rounded-lg bg-[#EADDE2] border border-[#DCD3C8] text-xs font-mono text-[#64283D]">
              {message}
            </div>
          )}

          <div className="pt-3 flex justify-end gap-2.5 border-t border-[#DCD3C8]">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-xs font-medium rounded-lg bg-[#E9DFD2] hover:bg-[#DCD3C8] text-[#29272B] transition"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="px-5 py-2 text-xs font-semibold rounded-lg bg-[#64283D] hover:bg-[#4A1D2E] text-[#FFFEFC] shadow-sm transition active:scale-[0.98]"
            >
              {isSubmitting ? 'Publishing...' : 'Publish to Kafka'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
