import React from 'react';
import { DataQualityRun } from '../types';
import { ShieldCheck, CheckCircle2, AlertOctagon } from 'lucide-react';

interface QualityProps {
  runs: DataQualityRun[];
}

export const DataQualityPanel: React.FC<QualityProps> = ({ runs }) => {
  return (
    <div className="rounded-xl border border-[#514850] bg-[#29272B] overflow-hidden shadow-md flex flex-col">
      <div className="px-5 py-3.5 border-b border-[#514850] bg-[#39343A] flex items-center justify-between">
        <div className="flex items-center gap-2">
          <ShieldCheck className="w-4 h-4 text-[#47745B]" />
          <h2 className="text-sm font-semibold text-[#FFFEFC] font-heading">
            Great Expectations 1.24.1 Data Quality Runs
          </h2>
        </div>
        <span className="text-xs text-[#B08A59] font-mono font-medium">
          Canonical Suite v1.0.0
        </span>
      </div>

      <div className="overflow-x-auto flex-1">
        <table className="w-full text-left text-xs text-[#EADDE2]">
          <thead className="bg-[#29272B] text-[#DCD3C8] uppercase font-mono text-[10px] tracking-wider border-b border-[#514850]">
            <tr>
              <th className="px-4 py-3">Run ID</th>
              <th className="px-4 py-3">Batch ID</th>
              <th className="px-4 py-3">Records (Total / Valid / Reject)</th>
              <th className="px-4 py-3">Pass Rate</th>
              <th className="px-4 py-3">Latency</th>
              <th className="px-4 py-3">Quality Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[#514850]/60 font-mono">
            {runs.length === 0 ? (
              <tr>
                <td colSpan={6} className="px-4 py-8 text-center text-[#77716D] font-sans">
                  No Great Expectations validation runs recorded.
                </td>
              </tr>
            ) : (
              runs.map((r) => (
                <tr key={r.run_id} className="hover:bg-[#39343A]/70 transition">
                  <td className="px-4 py-2.5 text-[#DCD3C8] truncate max-w-[140px] font-mono text-[11px]" title={r.run_id}>
                    {r.run_id}
                  </td>
                  <td className="px-4 py-2.5 font-bold text-[#FFFEFC]">
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
                    <span
                      className={`font-bold ${
                        r.success_rate >= 95 ? 'text-[#47745B]' : 'text-[#A87531]'
                      }`}
                    >
                      {r.success_rate.toFixed(1)}%
                    </span>
                  </td>
                  <td className="px-4 py-2.5 text-[#DCD3C8]">
                    {r.evaluation_time_ms.toFixed(1)}ms
                  </td>
                  <td className="px-4 py-2.5">
                    <span
                      className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded text-[10px] font-bold ${
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
  );
};
