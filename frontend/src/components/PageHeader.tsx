import React from 'react';
import { ChevronRight } from 'lucide-react';
import { NavPage } from '../types';

interface PageHeaderProps {
  pageId: NavPage;
  title: string;
  description: string;
  actions?: React.ReactNode;
}

const PAGE_SECTION_NAMES: Record<NavPage, string> = {
  overview: 'Platform Overview',
  ingestion: 'Telemetry Ingestion',
  explorer: 'Event Stream Explorer',
  analytics: 'Structured Streaming Analytics',
  quality: 'Great Expectations Suite',
  anomalies: 'Isolation Forest Anomaly Detection',
  monitoring: 'Pipeline Infrastructure & Fenced Ledger',
  storage: 'MinIO Parquet Lake & Manifests',
};

export const PageHeader: React.FC<PageHeaderProps> = ({
  pageId,
  title,
  description,
  actions,
}) => {
  return (
    <div className="flex flex-col md:flex-row md:items-center justify-between pb-6 mb-6 border-b border-[#DCD3C8] gap-4">
      <div>
        <div className="flex items-center gap-1.5 text-xs text-[#77716D] font-mono mb-1.5">
          <span>FlowSync Platform</span>
          <ChevronRight className="w-3.5 h-3.5 text-[#B08A59]" />
          <span className="text-[#64283D] font-semibold">{PAGE_SECTION_NAMES[pageId]}</span>
        </div>
        <h1 className="text-2xl font-bold font-heading text-[#29272B] tracking-tight">
          {title}
        </h1>
        <p className="text-xs text-[#77716D] font-sans mt-1 max-w-3xl">
          {description}
        </p>
      </div>

      {actions && <div className="flex items-center gap-2.5">{actions}</div>}
    </div>
  );
};

