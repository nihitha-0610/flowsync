import React from 'react';
import {
  Archive,
  Cpu,
  Database,
  Flame,
  LayoutDashboard,
  LineChart,
  RefreshCw,
  Send,
  ShieldCheck,
  Zap,
} from 'lucide-react';
import { NavPage, PipelineStats } from '../types';

interface TopbarProps {
  activePage: NavPage;
  onSelectPage: (page: NavPage) => void;
  onRefresh: () => void;
  isRefreshing: boolean;
  stats: PipelineStats | null;
  isBackendHealthy: boolean;
}

export const Topbar: React.FC<TopbarProps> = ({
  activePage,
  onSelectPage,
  onRefresh,
  isRefreshing,
  stats,
  isBackendHealthy,
}) => {
  const navItems: { id: NavPage; label: string; icon: React.ReactNode; badge?: number | string }[] = [
    { id: 'overview', label: 'Overview', icon: <LayoutDashboard className="w-4 h-4" /> },
    { id: 'ingestion', label: 'Data Ingestion', icon: <Send className="w-4 h-4" /> },
    {
      id: 'explorer',
      label: 'Event Explorer',
      icon: <Database className="w-4 h-4" />,
      badge: stats ? stats.valid_events_total : undefined,
    },
    { id: 'analytics', label: 'Stream Analytics', icon: <LineChart className="w-4 h-4" /> },
    {
      id: 'quality',
      label: 'Data Quality',
      icon: <ShieldCheck className="w-4 h-4" />,
      badge: stats && stats.invalid_events_total > 0 ? `${stats.invalid_events_total} rejects` : undefined,
    },
    {
      id: 'anomalies',
      label: 'AI Anomalies',
      icon: <Flame className="w-4 h-4" />,
      badge: stats && stats.anomalies_total > 0 ? stats.anomalies_total : undefined,
    },
    {
      id: 'monitoring',
      label: 'Pipeline Monitoring',
      icon: <Cpu className="w-4 h-4" />,
      badge: stats ? `b_${stats.successful_microbatches}` : undefined,
    },
    { id: 'storage', label: 'Storage Explorer', icon: <Archive className="w-4 h-4" /> },
  ];

  return (
    <header className="sticky top-0 z-50 bg-[#FFFEFC]/95 backdrop-blur-md border-b border-[#DCD3C8] shadow-sm select-none">
      {/* Top tier: Brand, Environment, Status & Quick Actions */}
      <div className="max-w-[1600px] mx-auto px-6 h-16 flex items-center justify-between gap-4">
        {/* Brand identity */}
        <div className="flex items-center gap-3.5 cursor-pointer" onClick={() => onSelectPage('overview')}>
          <div className="w-9 h-9 rounded-xl bg-[#64283D] flex items-center justify-center text-[#FFFEFC] shadow-sm ring-1 ring-[#B08A59]/40">
            <Zap className="w-5 h-5 text-[#B08A59] fill-[#B08A59]/20" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-heading font-extrabold text-lg tracking-tight text-[#64283D]">
                FlowSync
              </span>
              <span className="px-2 py-0.5 text-[10px] font-mono font-semibold uppercase tracking-wider bg-[#EADDE2] text-[#64283D] rounded-full border border-[#DCD3C8]">
                Enterprise
              </span>
            </div>
            <p className="text-[11px] text-[#77716D] font-sans -mt-0.5">
              Industrial IoT Stream Intelligence & Data Quality
            </p>
          </div>
        </div>

        {/* Center / Utility: Quick Pipeline Telemetry Counters */}
        <div className="hidden xl:flex items-center gap-4 text-xs font-mono">
          <div className="flex items-center gap-2 px-3 py-1 rounded-lg bg-[#F8F5F0] border border-[#DCD3C8]">
            <span className="text-[#77716D]">Processed:</span>
            <span className="font-bold text-[#47745B]">
              {stats?.valid_events_total ?? '—'}
            </span>
          </div>

          <div className="flex items-center gap-2 px-3 py-1 rounded-lg bg-[#F8F5F0] border border-[#DCD3C8]">
            <span className="text-[#77716D]">Quarantined:</span>
            <span className="font-bold text-[#A87531]">
              {stats?.invalid_events_total ?? '—'}
            </span>
          </div>

          <div className="flex items-center gap-2 px-3 py-1 rounded-lg bg-[#F8F5F0] border border-[#DCD3C8]">
            <span className="text-[#77716D]">Anomalies:</span>
            <span className="font-bold text-[#A74449]">
              {stats?.anomalies_total ?? '—'}
            </span>
          </div>

          <div className="flex items-center gap-2 px-3 py-1 rounded-lg bg-[#F8F5F0] border border-[#DCD3C8]">
            <span className="text-[#77716D]">Microbatches:</span>
            <span className="font-bold text-[#52758B]">
              {stats?.successful_microbatches ?? '—'}
            </span>
          </div>
        </div>

        {/* Right side controls */}
        <div className="flex items-center gap-3">
          {/* Engine Status indicator */}
          <div
            className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium border ${
              isBackendHealthy
                ? 'bg-[#47745B]/10 text-[#47745B] border-[#47745B]/30'
                : 'bg-[#A74449]/10 text-[#A74449] border-[#A74449]/30'
            }`}
          >
            <span
              className={`w-2 h-2 rounded-full ${
                isBackendHealthy ? 'bg-[#47745B] animate-pulse' : 'bg-[#A74449]'
              }`}
            />
            <span className="font-sans font-semibold text-[11px]">
              {isBackendHealthy ? 'Pipeline Live' : 'Backend Disconnected'}
            </span>
          </div>

          {/* Refresh action */}
          <button
            onClick={onRefresh}
            disabled={isRefreshing}
            title="Refresh All Stream & Database Metrics"
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-[#FFFEFC] hover:bg-[#E9DFD2] text-[#29272B] border border-[#DCD3C8] transition active:scale-95 shadow-2xs"
          >
            <RefreshCw className={`w-3.5 h-3.5 text-[#77716D] ${isRefreshing ? 'animate-spin text-[#64283D]' : ''}`} />
            <span className="hidden sm:inline">Refresh</span>
          </button>

          {/* Fast manual ingest shortcut button */}
          <button
            onClick={() => onSelectPage('ingestion')}
            className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg text-xs font-semibold bg-[#64283D] hover:bg-[#4A1D2E] text-[#FFFEFC] transition active:scale-95 shadow-sm"
          >
            <Send className="w-3.5 h-3.5 text-[#B08A59]" />
            <span>Ingest</span>
          </button>
        </div>
      </div>

      {/* Bottom tier: Horizontal Navigation Links */}
      <nav className="max-w-[1600px] mx-auto px-6 overflow-x-auto scrollbar-none flex items-center gap-1">
        {navItems.map((item) => {
          const isActive = activePage === item.id;
          return (
            <button
              key={item.id}
              onClick={() => onSelectPage(item.id)}
              className={`relative flex items-center gap-2 py-3 px-3.5 text-xs font-medium whitespace-nowrap transition-colors border-b-2 ${
                isActive
                  ? 'border-[#64283D] text-[#64283D] font-bold bg-[#64283D]/5'
                  : 'border-transparent text-[#77716D] hover:text-[#29272B] hover:bg-[#F8F5F0]'
              }`}
            >
              <span className={isActive ? 'text-[#64283D]' : 'text-[#77716D]'}>
                {item.icon}
              </span>
              <span>{item.label}</span>
              {item.badge !== undefined && (
                <span
                  className={`ml-1 px-1.5 py-0.2 rounded-full font-mono text-[10px] ${
                    isActive
                      ? 'bg-[#64283D] text-[#FFFEFC]'
                      : 'bg-[#E9DFD2] text-[#29272B]'
                  }`}
                >
                  {item.badge}
                </span>
              )}
            </button>
          );
        })}
      </nav>
    </header>
  );
};
