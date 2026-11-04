import React, { useState } from 'react';
import {
  FileBox,
  FolderTree,
  HardDrive,
  Lock,
} from 'lucide-react';
import { PageHeader } from '../components/PageHeader';
import { ManifestRecord } from '../types';

interface StoragePageProps {
  manifests: ManifestRecord[];
}

export const StorageExplorerPage: React.FC<StoragePageProps> = ({ manifests }) => {
  const [selectedBucket, setSelectedBucket] = useState<string>('flowsync-refined');

  const buckets = [
    {
      name: 'flowsync-refined',
      role: 'Analytical Parquet Lake',
      format: 'Snappy Parquet (Columnar)',
      partitioning: 'date=YYYY-MM-DD / hour=HH',
      description: 'Authoritative, deduplicated, and schema-validated telemetry events ready for SQL analytics and downstream ML pipelines.',
      samplePaths: [
        'events/date=2026-10-30/hour=15/part-00000.c000.snappy.parquet',
        'events/date=2026-10-30/hour=15/part-00001.c000.snappy.parquet',
        'manifests/batch_telemetry_stream_main_v1_7_att_tok_1.json',
      ],
    },
    {
      name: 'flowsync-raw',
      role: 'Raw Kafka Ingress Lake',
      format: 'Raw Parquet Dumps',
      partitioning: 'batches/batch_{id}.parquet',
      description: 'Immutable, exact-byte raw Kafka message payload dumps for complete replayability and disaster recovery.',
      samplePaths: [
        'batches/batch_1.parquet/part-00000-snappy.parquet',
        'batches/batch_2.parquet/part-00000-snappy.parquet',
        'batches/batch_5.parquet/_SUCCESS',
      ],
    },
    {
      name: 'flowsync-quarantine',
      role: 'Quarantine / DLQ Object Store',
      format: 'Snappy Parquet',
      partitioning: 'structural_rejects/batch_{id}.parquet',
      description: 'Corrupted JSON records and events violating Layer A syntax or Layer B contract invariants.',
      samplePaths: [
        'structural_rejects/batch_1.parquet/part-00000.parquet',
        'structural_rejects/batch_2.parquet/part-00000.parquet',
        'structural_rejects/_SUCCESS',
      ],
    },
    {
      name: 'flowsync-models',
      role: 'ML Model Registry',
      format: 'Joblib / Scikit-learn',
      partitioning: 'isolation_forest/{version}/',
      description: 'Serialized ML models, scikit-learn Isolation Forest estimators, and feature scalers scored in stream inference.',
      samplePaths: [
        'isolation_forest/v1/model.joblib (211,648 bytes)',
      ],
    },
    {
      name: 'flowsync-checkpoints',
      role: 'Spark Streaming Checkpoint State',
      format: 'HDFS-backed State Store',
      partitioning: 'spark/{query_id}/commits/',
      description: 'Delta commit logs, offset metadata, and checkpoint snapshots ensuring exactly-once processing across driver restarts.',
      samplePaths: [
        'spark/query_a_telemetry/commits/0..7',
        'spark/query_a_telemetry/offsets/0..7',
        'spark/query_a_telemetry/metadata',
      ],
    },
  ];

  const currentBucket = buckets.find((b) => b.name === selectedBucket) || buckets[0];

  return (
    <div className="space-y-6">
      <PageHeader
        pageId="storage"
        title="MinIO Parquet Analytical Lake & Object Hierarchy"
        description="Exploration of S3a object storage buckets, Snappy-compressed Parquet lake structures, and cryptographic manifest checksum verification."
      />

      {/* 1. Bucket Selection Strip */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-3">
        {buckets.map((b) => {
          const isSelected = selectedBucket === b.name;
          return (
            <button
              key={b.name}
              onClick={() => setSelectedBucket(b.name)}
              className={`p-4 rounded-xl border text-left transition flex flex-col justify-between ${
                isSelected
                  ? 'bg-[#64283D] border-[#64283D] text-[#FFFEFC] shadow-sm'
                  : 'bg-[#FFFEFC] border-[#DCD3C8] text-[#29272B] hover:border-[#B08A59]'
              }`}
            >
              <div>
                <div className="flex items-center justify-between mb-1.5">
                  <HardDrive className={`w-4 h-4 ${isSelected ? 'text-[#B08A59]' : 'text-[#64283D]'}`} />
                  <span className={`text-[10px] font-mono px-1.5 py-0.2 rounded ${isSelected ? 'bg-[#FFFEFC]/20' : 'bg-[#F8F5F0]'}`}>
                    S3a
                  </span>
                </div>
                <h4 className="font-mono font-bold text-xs truncate" title={b.name}>
                  {b.name}
                </h4>
              </div>
              <p className={`text-[11px] font-sans mt-2 ${isSelected ? 'text-[#EADDE2]' : 'text-[#77716D]'}`}>
                {b.role}
              </p>
            </button>
          );
        })}
      </div>

      {/* 2. Detailed Selected Bucket Overview */}
      <div className="p-6 rounded-xl bg-[#FFFEFC] border border-[#DCD3C8] shadow-xs space-y-4">
        <div className="flex flex-col md:flex-row md:items-center justify-between pb-4 border-b border-[#DCD3C8] gap-3">
          <div>
            <div className="flex items-center gap-2">
              <span className="font-mono font-bold text-base text-[#64283D]">
                s3a://{currentBucket.name}/
              </span>
              <span className="px-2 py-0.5 rounded text-[11px] font-mono font-semibold bg-[#47745B]/10 text-[#47745B] border border-[#47745B]/30">
                ACTIVE BUCKET
              </span>
            </div>
            <p className="text-xs text-[#77716D] font-sans mt-1">
              {currentBucket.description}
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-2 font-mono text-xs">
            <span className="px-2.5 py-1 rounded-lg bg-[#F8F5F0] border border-[#DCD3C8] text-[#29272B]">
              Format: <strong>{currentBucket.format}</strong>
            </span>
            <span className="px-2.5 py-1 rounded-lg bg-[#F8F5F0] border border-[#DCD3C8] text-[#64283D]">
              Partitioning: <strong>{currentBucket.partitioning}</strong>
            </span>
          </div>
        </div>

        {/* Directory Structure & Sample Object Paths */}
        <div>
          <h4 className="font-heading font-bold text-xs text-[#29272B] mb-2 flex items-center gap-1.5">
            <FolderTree className="w-4 h-4 text-[#B08A59]" />
            <span>Sample Object Keys & Hierarchy:</span>
          </h4>

          <div className="p-4 rounded-xl bg-[#29272B] border border-[#514850] text-[#EADDE2] font-mono text-xs space-y-2">
            {currentBucket.samplePaths.map((p, idx) => (
              <div key={idx} className="flex items-center gap-2">
                <FileBox className="w-3.5 h-3.5 text-[#B08A59] shrink-0" />
                <span className="truncate">{p}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* 3. Authoritative Manifest Commit Tree */}
      <div className="rounded-xl border border-[#514850] bg-[#29272B] overflow-hidden shadow-md">
        <div className="px-5 py-3.5 border-b border-[#514850] bg-[#39343A] flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Lock className="w-4 h-4 text-[#B08A59]" />
            <h2 className="text-sm font-semibold text-[#FFFEFC] font-heading">
              Authoritative Manifest Audit Trail in s3a://flowsync-refined/manifests/
            </h2>
          </div>
          <span className="text-xs text-[#DCD3C8] font-mono">
            {manifests.length} batch ledger commits
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs font-mono text-[#EADDE2]">
            <thead className="bg-[#29272B] text-[#DCD3C8] uppercase text-[10px] tracking-wider border-b border-[#514850]">
              <tr>
                <th className="px-4 py-3">Batch ID</th>
                <th className="px-4 py-3">Attempt ID</th>
                <th className="px-4 py-3">Fencing Token</th>
                <th className="px-4 py-3">MinIO Path</th>
                <th className="px-4 py-3">SHA-256 Digest</th>
                <th className="px-4 py-3">Commit Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#514850]/50">
              {manifests.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-4 py-8 text-center text-[#77716D] font-sans">
                    No manifest ledger commits recorded.
                  </td>
                </tr>
              ) : (
                manifests.map((m) => (
                  <tr key={`${m.batch_id}-${m.attempt_id}`} className="hover:bg-[#39343A]/70 transition">
                    <td className="px-4 py-2.5 font-bold text-[#B08A59]">
                      batch_{m.batch_id}
                    </td>
                    <td className="px-4 py-2.5 text-[#DCD3C8]">{m.attempt_id}</td>
                    <td className="px-4 py-2.5">
                      <span className="px-2 py-0.5 rounded font-bold bg-[#64283D]/40 text-[#EADDE2] border border-[#64283D]">
                        Token: {m.fencing_token}
                      </span>
                    </td>
                    <td className="px-4 py-2.5 text-[#DCD3C8] truncate max-w-sm" title={m.manifest_path}>
                      {m.manifest_path}
                    </td>
                    <td className="px-4 py-2.5 text-[#77716D] truncate max-w-[140px]" title={m.manifest_checksum}>
                      {m.manifest_checksum || '—'}
                    </td>
                    <td className="px-4 py-2.5">
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-[#47745B]/20 text-[#47745B] border border-[#47745B]/40">
                        {m.status}
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
