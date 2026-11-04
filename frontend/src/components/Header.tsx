import React from 'react';
import { Activity, RefreshCw, Send } from 'lucide-react';

interface HeaderProps {
  onRefresh: () => void;
  onOpenIngest: () => void;
  isRefreshing: boolean;
}

export const Header: React.FC<HeaderProps> = ({ onRefresh, onOpenIngest, isRefreshing }) => {
  return (
    <header className="border-b border-[#DCD3C8] bg-[#FFFEFC]/90 backdrop-blur-md sticky top-0 z-50 px-6 py-4 flex items-center justify-between shadow-sm">
      <div className="flex items-center space-x-3.5">
        <div className="p-2.5 bg-[#64283D] rounded-xl text-[#FFFEFC] shadow-sm">
          <Activity className="w-5 h-5 text-[#B08A59]" />
        </div>
        <div>
          <div className="flex items-center gap-2.5">
            <h1 className="text-xl font-bold tracking-tight text-[#64283D] font-heading">
              FlowSync Control Plane
            </h1>
            <span className="px-2 py-0.5 text-[10px] font-mono font-semibold uppercase tracking-wider bg-[#EADDE2] text-[#64283D] rounded-full border border-[#DCD3C8]">
              Live Engine
            </span>
          </div>
          <p className="text-xs text-[#77716D] flex items-center gap-2 mt-0.5 font-sans">
            <span className="inline-block w-2 h-2 rounded-full bg-[#47745B] animate-pulse"></span>
            Real-Time Streaming Analytics & AI Anomaly Detection
          </p>
        </div>
      </div>

      <div className="flex items-center space-x-3">
        <button
          onClick={onOpenIngest}
          className="flex items-center space-x-2 px-4 py-2 text-xs font-semibold rounded-lg bg-[#64283D] hover:bg-[#4A1D2E] text-[#FFFEFC] shadow-sm transition active:scale-[0.98]"
        >
          <Send className="w-3.5 h-3.5" />
          <span>Ingest Telemetry</span>
        </button>

        <button
          onClick={onRefresh}
          disabled={isRefreshing}
          className="flex items-center space-x-1.5 px-3.5 py-2 text-xs font-medium rounded-lg bg-[#FFFEFC] hover:bg-[#E9DFD2] text-[#29272B] border border-[#DCD3C8] transition active:scale-[0.98]"
        >
          <RefreshCw className={`w-3.5 h-3.5 text-[#77716D] ${isRefreshing ? 'animate-spin' : ''}`} />
          <span>Refresh</span>
        </button>
      </div>
    </header>
  );
};
