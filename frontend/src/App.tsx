import React, { useEffect, useState } from 'react';
import { Topbar } from './components/Topbar';
import { OverviewPage } from './pages/OverviewPage';
import { DataIngestionPage } from './pages/DataIngestionPage';
import { EventExplorerPage } from './pages/EventExplorerPage';
import { StreamAnalyticsPage } from './pages/StreamAnalyticsPage';
import { DataQualityPage } from './pages/DataQualityPage';
import { AnomalyDetectionPage } from './pages/AnomalyDetectionPage';
import { PipelineMonitoringPage } from './pages/PipelineMonitoringPage';
import { StorageExplorerPage } from './pages/StorageExplorerPage';
import {
  checkBackendHealth,
  fetchAnomalies,
  fetchInvalidEvents,
  fetchManifests,
  fetchQualityRuns,
  fetchQualitySuites,
  fetchRecentEvents,
  fetchStats,
  fetchWindowMetrics,
} from './services/api';
import {
  AnomalyDetection,
  DataQualityRun,
  InvalidEvent,
  ManifestRecord,
  NavPage,
  PipelineStats,
  QualitySuite,
  TelemetryEvent,
  WindowMetric,
} from './types';

const getPageFromHash = (): NavPage => {
  const hash = window.location.hash.replace('#', '') as NavPage;
  const validPages: NavPage[] = [
    'overview',
    'ingestion',
    'explorer',
    'analytics',
    'quality',
    'anomalies',
    'monitoring',
    'storage',
  ];
  return validPages.includes(hash) ? hash : 'overview';
};

export const App: React.FC = () => {
  const [activePage, setActivePage] = useState<NavPage>(getPageFromHash);
  const [stats, setStats] = useState<PipelineStats | null>(null);
  const [events, setEvents] = useState<TelemetryEvent[]>([]);
  const [invalidEvents, setInvalidEvents] = useState<InvalidEvent[]>([]);
  const [windows, setWindows] = useState<WindowMetric[]>([]);
  const [qualityRuns, setQualityRuns] = useState<DataQualityRun[]>([]);
  const [qualitySuites, setQualitySuites] = useState<QualitySuite[]>([]);
  const [manifests, setManifests] = useState<ManifestRecord[]>([]);
  const [anomalies, setAnomalies] = useState<AnomalyDetection[]>([]);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [isBackendHealthy, setIsBackendHealthy] = useState(true);
  const [errorNotice, setErrorNotice] = useState<string | null>(null);

  useEffect(() => {
    const handleHashChange = () => {
      setActivePage(getPageFromHash());
    };
    window.addEventListener('hashchange', handleHashChange);
    return () => window.removeEventListener('hashchange', handleHashChange);
  }, []);

  const handleSelectPage = (page: NavPage) => {
    setActivePage(page);
    window.location.hash = page;
  };

  const loadAllData = async () => {
    setIsRefreshing(true);
    const errors: string[] = [];

    const [
      healthData,
      sData,
      eData,
      invData,
      wData,
      qData,
      suiteData,
      manData,
      aData,
    ] = await Promise.all([
      checkBackendHealth().catch(() => ({ status: 'down' })),
      fetchStats().catch((err) => { errors.push(`Stats: ${err.message}`); return null; }),
      fetchRecentEvents().catch((err) => { errors.push(`Events: ${err.message}`); return []; }),
      fetchInvalidEvents().catch((err) => { errors.push(`DLQ: ${err.message}`); return []; }),
      fetchWindowMetrics().catch((err) => { errors.push(`Windows: ${err.message}`); return []; }),
      fetchQualityRuns().catch((err) => { errors.push(`DQ Runs: ${err.message}`); return []; }),
      fetchQualitySuites().catch((err) => { errors.push(`Suites: ${err.message}`); return []; }),
      fetchManifests().catch((err) => { errors.push(`Manifests: ${err.message}`); return []; }),
      fetchAnomalies().catch((err) => { errors.push(`Anomalies: ${err.message}`); return []; }),
    ]);

    setIsBackendHealthy(healthData.status === 'healthy' || healthData.status === 'operational');

    if (sData) setStats(sData);
    if (eData) setEvents(eData);
    if (invData) setInvalidEvents(invData);
    if (wData) setWindows(wData);
    if (qData) setQualityRuns(qData);
    if (suiteData) setQualitySuites(suiteData);
    if (manData) setManifests(manData);
    if (aData) setAnomalies(aData);

    if (errors.length > 0) {
      setErrorNotice(errors.join(' | '));
    } else {
      setErrorNotice(null);
    }
    setIsRefreshing(false);
  };

  useEffect(() => {
    loadAllData();
    const interval = setInterval(loadAllData, 5000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="min-h-screen bg-[#F8F5F0] text-[#29272B] flex flex-col font-sans selection:bg-[#EADDE2] selection:text-[#64283D]">
      {/* 1. Universal Enterprise Topbar */}
      <Topbar
        activePage={activePage}
        onSelectPage={handleSelectPage}
        onRefresh={loadAllData}
        isRefreshing={isRefreshing}
        stats={stats}
        isBackendHealthy={isBackendHealthy}
      />

      {/* 2. Main Page Content Workspace */}
      <main className="flex-1 max-w-[1600px] w-full mx-auto p-6 lg:p-8">
        {/* Error Alert Banner if an API call fails */}
        {errorNotice && (
          <div className="mb-6 p-4 rounded-xl bg-[#A74449]/10 border border-[#A74449]/30 text-[#A74449] text-xs font-mono flex items-center justify-between">
            <span>Notice: {errorNotice}</span>
            <button
              onClick={() => setErrorNotice(null)}
              className="text-[#A74449] hover:underline font-bold ml-2 font-sans"
            >
              Dismiss
            </button>
          </div>
        )}

        {/* View Router */}
        {activePage === 'overview' && (
          <OverviewPage
            stats={stats}
            events={events}
            anomalies={anomalies}
            onNavigate={handleSelectPage}
          />
        )}

        {activePage === 'ingestion' && (
          <DataIngestionPage
            onEventIngested={loadAllData}
            recentEvents={events}
          />
        )}

        {activePage === 'explorer' && (
          <EventExplorerPage
            events={events}
            invalidEvents={invalidEvents}
          />
        )}

        {activePage === 'analytics' && (
          <StreamAnalyticsPage
            metrics={windows}
          />
        )}

        {activePage === 'quality' && (
          <DataQualityPage
            runs={qualityRuns}
            suites={qualitySuites}
          />
        )}

        {activePage === 'anomalies' && (
          <AnomalyDetectionPage
            anomalies={anomalies}
          />
        )}

        {activePage === 'monitoring' && (
          <PipelineMonitoringPage
            stats={stats}
            manifests={manifests}
            isHealthy={isBackendHealthy}
          />
        )}

        {activePage === 'storage' && (
          <StorageExplorerPage
            manifests={manifests}
          />
        )}
      </main>

      {/* 3. Enterprise Platform Footer */}
      <footer className="border-t border-[#DCD3C8] bg-[#FFFEFC] py-4 px-6 text-center text-xs text-[#77716D] font-mono">
        <div className="max-w-[1600px] mx-auto flex flex-col sm:flex-row items-center justify-between gap-2">
          <span>
            FlowSync Enterprise v1.0.0 — Apache Kafka 3.8.0 • PySpark 3.5.1 • Great Expectations 1.24.1 • Scikit-learn
          </span>
          <span className="text-[#B08A59]">
            PostgreSQL 16 ACID Sinks • MinIO Analytical Parquet Lake
          </span>
        </div>
      </footer>
    </div>
  );
};

export default App;
