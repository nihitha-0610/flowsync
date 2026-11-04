import React from 'react';
import { AnomalyDetection } from '../types';
import { Flame } from 'lucide-react';

interface AnomalyProps {
  anomalies: AnomalyDetection[];
}

export const AnomalyFeed: React.FC<AnomalyProps> = ({ anomalies }) => {
  return (
    <div className="rounded-xl border border-[#514850] bg-[#29272B] overflow-hidden shadow-md flex flex-col">
      <div className="px-5 py-3.5 border-b border-[#514850] bg-[#39343A] flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Flame className="w-4 h-4 text-[#A74449]" />
          <h2 className="text-sm font-semibold text-[#FFFEFC] font-heading">
            AI Anomaly Detections (Isolation Forest)
          </h2>
        </div>
        <span className="text-xs text-[#A74449] font-mono font-bold">
          {anomalies.length} outliers detected
        </span>
      </div>

      <div className="divide-y divide-[#514850]/60 max-h-[360px] overflow-y-auto flex-1">
        {anomalies.length === 0 ? (
          <div className="p-8 text-center text-[#77716D] text-xs font-sans">
            No sensor anomalies detected. Operating within nominal baseline distribution.
          </div>
        ) : (
          anomalies.map((a) => (
            <div key={a.anomaly_id} className="p-4 hover:bg-[#39343A]/70 transition flex items-start justify-between">
              <div>
                <div className="flex items-center gap-2">
                  <span className="font-mono font-bold text-[#FFFEFC] text-xs">{a.device_id}</span>
                  <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-[#A74449]/20 text-[#A74449] border border-[#A74449]/40">
                    ANOMALY
                  </span>
                  <span className="text-xs text-[#DCD3C8] font-mono">
                    Score: {a.anomaly_score.toFixed(3)} ({(a.confidence * 100).toFixed(1)}% conf)
                  </span>
                </div>
                <div className="mt-1 text-xs text-[#EADDE2] font-sans">
                  <span className="text-[#DCD3C8]">Primary Driver:</span>{' '}
                  <span className="font-bold text-[#B08A59] capitalize font-mono">{a.primary_driver}</span>
                </div>
                <div className="mt-2 flex flex-wrap gap-2 text-[10px] font-mono text-[#DCD3C8]">
                  {Object.entries(a.feature_contributions || {}).map(([feat, dev]) => (
                    <span key={feat} className="px-2 py-0.5 bg-[#39343A] rounded border border-[#514850]">
                      {feat}: <strong className="text-[#A74449]">{dev}σ</strong>
                    </span>
                  ))}
                </div>
              </div>
              <span className="text-[11px] font-mono text-[#77716D]">
                {new Date(a.timestamp).toLocaleTimeString()}
              </span>
            </div>
          ))
        )}
      </div>
    </div>
  );
};
