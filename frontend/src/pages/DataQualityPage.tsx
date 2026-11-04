import React, { useState } from 'react';
import {
  AlertOctagon,
  CheckCircle2,
  Fingerprint,
  Layers,
  Search,
  ShieldCheck,
} from 'lucide-react';
import { PageHeader } from '../components/PageHeader';
import { DataQualityRun, QualitySuite } from '../types';

interface QualityPageProps {
  runs: DataQualityRun[];
  suites: QualitySuite[];
}

export const DataQualityPage: React.FC<QualityPageProps> = ({ runs, suites }) => {
  const [selectedSuite, setSelectedSuite] = useState<QualitySuite | null>(
    suites.length > 0 ? suites[0] : null
  );
  const [ruleSearch, setRuleSearch] = useState('');

  const activeSuite = selectedSuite || (suites.length > 0 ? suites[0] : null);

  const filteredRules = activeSuite?.canonical_rules?.filter((r) => {
    const str = `${r.type} ${JSON.stringify(r.kwargs)}`.toLowerCase();
    return str.includes(ruleSearch.toLowerCase());
  }) ?? [];

  const avgPassRate = runs.length
    ? (runs.reduce((acc, r) => acc + r.success_rate, 0) / runs.length).toFixed(1)
    : '100.0';

  const avgLatency = runs.length
    ? (runs.reduce((acc, r) => acc + r.evaluation_time_ms, 0) / runs.length).toFixed(0)
    : '0';

  return (
    <div className="space-y-6">
      <PageHeader
        pageId="quality"
        title="Great Expectations 1.24.1 Data Quality Suite"
        description="Every Spark micro-batch is evaluated in-memory before relational persistence. Records violating canonical invariants are quarantined to events_invalid, preserving audit trail integrity."
      />

      {/* 1. Quality Metric Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="p-4 rounded-xl bg-[#FFFEFC] border border-[#DCD3C8] shadow-xs">
          <span className="text-xs font-medium text-[#77716D]">Validation Runs Evaluated</span>
          <div className="mt-1.5 text-2xl font-bold font-mono text-[#29272B]">
            {runs.length}
          </div>
          <span className="text-[11px] text-[#47745B]">Microbatch Quality Sinks</span>
        </div>

        <div className="p-4 rounded-xl bg-[#FFFEFC] border border-[#DCD3C8] shadow-xs">
          <span className="text-xs font-medium text-[#77716D]">Average Pass Rate</span>
          <div className="mt-1.5 text-2xl font-bold font-mono text-[#47745B]">
            {avgPassRate}%
          </div>
          <span className="text-[11px] text-[#77716D]">Zero Critical Drift</span>
        </div>

        <div className="p-4 rounded-xl bg-[#FFFEFC] border border-[#DCD3C8] shadow-xs">
          <span className="text-xs font-medium text-[#77716D]">Average Evaluation Latency</span>
          <div className="mt-1.5 text-2xl font-bold font-mono text-[#52758B]">
            {avgLatency} ms
          </div>
          <span className="text-[11px] text-[#77716D]">In-Memory Driver Scoring</span>
        </div>

        <div className="p-4 rounded-xl bg-[#FFFEFC] border border-[#DCD3C8] shadow-xs">
          <span className="text-xs font-medium text-[#77716D]">Active Expectation Suite</span>
          <div className="mt-1.5 text-base font-bold font-mono text-[#64283D] truncate">
            {activeSuite?.suite_name ?? 'flowsync_canonical'}
          </div>
          <span className="text-[11px] text-[#B08A59] font-mono">
            {activeSuite?.expectation_count ?? 19} Invariant Rules
          </span>
        </div>
      </div>

      {/* 2. Registered Expectation Suite Invariants */}
      <div className="p-6 rounded-xl bg-[#FFFEFC] border border-[#DCD3C8] shadow-xs space-y-4">
        <div className="flex flex-col md:flex-row md:items-center justify-between pb-4 border-b border-[#DCD3C8] gap-3">
          <div className="flex items-center gap-2.5">
            <ShieldCheck className="w-5 h-5 text-[#47745B]" />
            <div>
              <h3 className="font-heading font-bold text-sm text-[#29272B]">
                Canonical Expectation Suite Specification ({activeSuite?.suite_name} v{activeSuite?.suite_version})
              </h3>
              <p className="text-xs text-[#77716D]">
                Layer B structural ranges and Layer C statistical bounds registered in PostgreSQL metadata.
              </p>
            </div>
          </div>

          {/* Suite Fingerprint Pill */}
          <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-[#F8F5F0] border border-[#DCD3C8] font-mono text-[11px] text-[#64283D]">
            <Fingerprint className="w-3.5 h-3.5 text-[#B08A59]" />
            <span className="truncate max-w-[180px]" title={activeSuite?.suite_fingerprint}>
              {activeSuite?.suite_fingerprint ? `fp: ${activeSuite.suite_fingerprint.slice(0, 16)}...` : 'Deterministic Hash'}
            </span>
          </div>
        </div>

        {/* Suite selector (if multiple) */}
        {suites.length > 1 && (
          <div className="flex gap-2">
            {suites.map((s) => (
              <button
                key={s.suite_name}
                onClick={() => setSelectedSuite(s)}
                className={`px-3 py-1 text-xs rounded-md font-mono transition ${
                  activeSuite?.suite_name === s.suite_name
                    ? 'bg-[#64283D] text-[#FFFEFC]'
                    : 'bg-[#F8F5F0] text-[#77716D] hover:bg-[#EADDE2]'
                }`}
              >
                {s.suite_name} (v{s.suite_version})
              </button>
            ))}
          </div>
        )}

        {/* Rule Search Filter */}
        <div className="flex items-center justify-between gap-4">
          <div className="relative flex-1 max-w-sm">
            <Search className="w-3.5 h-3.5 text-[#77716D] absolute left-3 top-2.5" />
            <input
              type="text"
              placeholder="Search expectation rules..."
              value={ruleSearch}
              onChange={(e) => setRuleSearch(e.target.value)}
              className="w-full pl-8 pr-3 py-1.5 text-xs bg-[#F8F5F0] border border-[#DCD3C8] rounded-lg text-[#29272B] font-mono focus:border-[#64283D] focus:outline-none"
            />
          </div>
          <span className="text-xs font-mono text-[#77716D]">
            Showing {filteredRules.length} of {activeSuite?.canonical_rules?.length ?? 19} rules
          </span>
        </div>

        {/* Rules Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          {filteredRules.map((rule, idx) => (
            <div
              key={idx}
              className="p-3.5 rounded-lg bg-[#F8F5F0] border border-[#DCD3C8] flex flex-col justify-between text-xs"
            >
              <div>
                <span className="font-mono text-[11px] font-bold text-[#64283D]">
                  {rule.type.replace(/^expect_/, '')}
                </span>
                <div className="mt-1.5 font-mono text-[10px] text-[#77716D] bg-[#FFFEFC] p-2 rounded border border-[#DCD3C8] overflow-x-auto">
                  {Object.entries(rule.kwargs).map(([k, v]) => (
                    <div key={k} className="flex justify-between">
                      <span className="font-semibold text-[#29272B]">{k}:</span>
                      <span className="text-[#64283D] font-mono ml-2 truncate max-w-[150px]" title={String(v)}>
                        {String(v)}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
              <div className="mt-2 pt-1 border-t border-[#DCD3C8] flex items-center justify-between text-[10px]">
                <span className="text-[#47745B] font-semibold flex items-center gap-1">
                  <CheckCircle2 className="w-3 h-3" />
                  Active Invariant
                </span>
                <span className="text-[#77716D] font-mono">Rule #{idx + 1}</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* 3. Validation Run History Table */}
      <div className="rounded-xl border border-[#514850] bg-[#29272B] overflow-hidden shadow-md">
        <div className="px-5 py-3.5 border-b border-[#514850] bg-[#39343A] flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Layers className="w-4 h-4 text-[#B08A59]" />
            <h2 className="text-sm font-semibold text-[#FFFEFC] font-heading">
              Micro-batch Validation Execution Ledger
            </h2>
          </div>
          <span className="text-xs text-[#DCD3C8] font-mono">
            {runs.length} batches evaluated
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs font-mono text-[#EADDE2]">
            <thead className="bg-[#29272B] text-[#DCD3C8] uppercase text-[10px] tracking-wider border-b border-[#514850]">
              <tr>
                <th className="px-4 py-3">Run ID</th>
                <th className="px-4 py-3">Batch ID</th>
                <th className="px-4 py-3">Records (Total / Valid / Rejects)</th>
                <th className="px-4 py-3">Pass Rate</th>
                <th className="px-4 py-3">Latency</th>
                <th className="px-4 py-3">Evaluated At (UTC)</th>
                <th className="px-4 py-3">Quality Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#514850]/50">
              {runs.length === 0 ? (
                <tr>
                  <td colSpan={7} className="px-4 py-8 text-center text-[#77716D] font-sans">
                    No Great Expectations validation runs recorded.
                  </td>
                </tr>
              ) : (
                runs.map((r) => (
                  <tr key={r.run_id} className="hover:bg-[#39343A]/70 transition">
                    <td className="px-4 py-2.5 text-[#DCD3C8] truncate max-w-[160px]" title={r.run_id}>
                      {r.run_id}
                    </td>
                    <td className="px-4 py-2.5 font-bold text-[#B08A59]">
                      batch_{r.batch_id}
                    </td>
                    <td className="px-4 py-2.5">
                      <span className="text-[#FFFEFC]">{r.total_records}</span>
                      <span className="text-[#77716D] mx-1">/</span>
                      <span className="text-[#47745B] font-semibold">{r.valid_records}</span>
                      <span className="text-[#77716D] mx-1">/</span>
                      <span className={r.invalid_records > 0 ? 'text-[#A87531] font-bold' : 'text-[#77716D]'}>
                        {r.invalid_records}
                      </span>
                    </td>
                    <td className="px-4 py-2.5">
                      <span className={`font-bold ${r.success_rate >= 95 ? 'text-[#47745B]' : 'text-[#A87531]'}`}>
                        {r.success_rate.toFixed(1)}%
                      </span>
                    </td>
                    <td className="px-4 py-2.5 text-[#DCD3C8]">
                      {r.evaluation_time_ms.toFixed(1)} ms
                    </td>
                    <td className="px-4 py-2.5 text-[#77716D]">
                      {new Date(r.evaluated_at).toLocaleTimeString()}
                    </td>
                    <td className="px-4 py-2.5">
                      <span
                        className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded text-[10px] font-bold ${
                          r.quality_status === 'PASSED'
                            ? 'bg-[#47745B]/20 text-[#47745B] border border-[#47745B]/40'
                            : 'bg-[#A87531]/20 text-[#A87531] border border-[#A87531]/40'
                        }`}
                      >
                        {r.quality_status === 'PASSED' ? (
                          <CheckCircle2 className="w-3 h-3" />
                        ) : (
                          <AlertOctagon className="w-3 h-3" />
                        )}
                        {r.quality_status}
                      </span>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
