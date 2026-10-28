/**
 * BatchDetection.jsx
 * CSV file upload page for bulk transaction fraud analysis.
 * Shows results with stats, chart, and downloadable output.
 */

import React, { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { PieChart, Pie, Cell, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import Card from '../components/UI/Card';
import StatCard from '../components/UI/StatCard';
import DataTable from '../components/UI/DataTable';
import Badge from '../components/UI/Badge';
import { analyzeBatchTransactions } from '../services/api';
import { useToast } from '../components/UI/Toast';
import { UploadCloud, FileText, FolderOpen } from 'lucide-react';

const PIE_COLORS = ['#ef4444', '#10b981'];

// ── Progress Bar Component ─────────────────────────────────────────────────────
function ProgressBar({ progress }) {
  return (
    <div>
      <div className="flex-between mb-8">
        <span style={{ fontSize: 13, color: 'var(--text-secondary)' }}>Processing...</span>
        <span style={{ fontSize: 13, fontWeight: 600, color: 'var(--accent-blue)' }}>{progress}%</span>
      </div>
      <div className="progress-bar-wrap">
        <div
          className="progress-bar-fill blue"
          style={{ width: `${progress}%`, transition: 'width 0.4s ease' }}
        />
      </div>
    </div>
  );
}

// ── Generate CSV from results ──────────────────────────────────────────────────
function downloadResultsCSV(results) {
  if (!results?.length) return;
  const headers = ['Row', 'Transaction_ID', 'Prediction', 'Fraud_Probability', 'Risk_Level'];
  const rows = results.map((r, i) => [
    i + 1,
    r.transaction_id || r.id || `ROW-${i + 1}`,
    r.prediction,
    typeof r.fraud_probability !== 'undefined' ? r.fraud_probability : r.probability,
    r.risk_level,
  ]);
  const csv = [headers, ...rows].map((row) => row.join(',')).join('\n');
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = `fraudguard_batch_results_${Date.now()}.csv`;
  link.click();
  URL.revokeObjectURL(url);
}

// ── Table Columns ──────────────────────────────────────────────────────────────
const RESULT_COLUMNS = [
  { key: '_row', label: '#', render: (_, row, idx) => idx + 1 },
  { key: 'transaction_id', label: 'Transaction ID', primary: true, render: (val, row, idx) => val || `ROW-${idx + 1}` },
  {
    key: 'prediction',
    label: 'Prediction',
    render: (val) => <Badge type={val === 1 || val === 'fraud' ? 'fraud' : 'legitimate'} />,
  },
  {
    key: 'fraud_probability',
    label: 'Fraud Probability',
    render: (val, row) => {
      const raw = val ?? row.probability ?? 0;
      const pct = (parseFloat(raw) * 100).toFixed(1);
      return (
        <div className="prob-bar-wrap">
          <div className="prob-bar-track">
            <div
              className="prob-bar-fill"
              style={{
                width: `${pct}%`,
                background: parseFloat(pct) > 70 ? 'var(--danger)' : parseFloat(pct) > 40 ? 'var(--warning)' : 'var(--success)',
              }}
            />
          </div>
          <span className="prob-value">{pct}%</span>
        </div>
      );
    },
  },
  {
    key: 'risk_level',
    label: 'Risk Level',
    render: (val) => <Badge type={val || 'low'} />,
  },
];

// ── Main Component ─────────────────────────────────────────────────────────────
export default function BatchDetection() {
  const toast = useToast();

  const [file, setFile]         = useState(null);
  const [loading, setLoading]   = useState(false);
  const [progress, setProgress] = useState(0);
  const [results, setResults]   = useState(null);
  const [apiError, setApiError] = useState(null);

  // ── Dropzone Setup ───────────────────────────────────────────────────────────
  const onDrop = useCallback((acceptedFiles, rejectedFiles) => {
    if (rejectedFiles.length > 0) {
      toast.error('Only .csv files are accepted.', 'Invalid File');
      return;
    }
    if (acceptedFiles.length > 0) {
      setFile(acceptedFiles[0]);
      setResults(null);
      setApiError(null);
      toast.info(`File "${acceptedFiles[0].name}" loaded. Ready to analyze.`);
    }
  }, [toast]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'text/csv': ['.csv'] },
    multiple: false,
    maxSize: 50 * 1024 * 1024, // 50MB
  });

  // ── Submit ────────────────────────────────────────────────────────────────────
  const handleAnalyze = async () => {
    if (!file) {
      toast.error('Please upload a CSV file first.', 'No File');
      return;
    }

    setLoading(true);
    setProgress(0);
    setApiError(null);
    setResults(null);

    // Simulate progress bar while waiting for API
    const progressInterval = setInterval(() => {
      setProgress((prev) => Math.min(prev + Math.random() * 15, 90));
    }, 400);

    try {
      const formData = new FormData();
      formData.append('file', file);
      const data = await analyzeBatchTransactions(formData);
      setProgress(100);
      const rows = data.predictions || data.results || data.data || [];
      setResults(rows);
      toast.success(`Analyzed ${rows.length} transactions successfully.`, 'Batch Complete');
    } catch (err) {
      setApiError(err.userMessage || 'Failed to process the batch file.');
      toast.error(err.userMessage || 'Batch analysis failed.', 'Error');
    } finally {
      clearInterval(progressInterval);
      setLoading(false);
    }
  };

  // ── Compute Summary Stats ────────────────────────────────────────────────────
  const getStats = () => {
    if (!results) return null;
    const total = results.length;
    const fraud = results.filter((r) => r.prediction === 'fraud' || r.prediction === 1).length;
    const legit = total - fraud;
    const rate  = total > 0 ? ((fraud / total) * 100).toFixed(2) : '0.00';
    return { total, fraud, legit, rate };
  };

  const stats = getStats();

  return (
    <div>
      {/* ── Upload Card ── */}
      <Card title="Upload Transactions CSV" className="mb-20">
        {/* Dropzone */}
        <div
          {...getRootProps()}
          className={`dropzone ${isDragActive ? 'active' : ''} ${file ? 'has-file' : ''}`}
        >
          <input {...getInputProps()} />
          <div className="dropzone-icon" style={{ display: 'flex', justifyContent: 'center', marginBottom: 12 }}>
            {file ? <FileText size={42} color="var(--success)" /> : isDragActive ? <FolderOpen size={42} color="var(--accent-blue)" /> : <UploadCloud size={42} color="var(--text-muted)" />}
          </div>
          {file ? (
            <>
              <div className="dropzone-title" style={{ color: 'var(--success)' }}>
                 {file.name}
              </div>
              <div className="dropzone-sub">
                {(file.size / 1024).toFixed(1)} KB — Click or drag to replace
              </div>
            </>
          ) : isDragActive ? (
            <div className="dropzone-title">Drop it here!</div>
          ) : (
            <>
              <div className="dropzone-title">Drag & Drop your CSV file here</div>
              <div className="dropzone-sub">or click to browse — .csv files only (max 50MB)</div>
            </>
          )}
        </div>

        {/* Progress Bar */}
        {loading && (
          <div style={{ marginTop: 20 }}>
            <ProgressBar progress={Math.round(progress)} />
          </div>
        )}

        {/* Error */}
        {apiError && (
          <div style={{
            marginTop: 16,
            padding: '12px 16px',
            background: 'rgba(239,68,68,0.08)',
            border: '1px solid rgba(239,68,68,0.25)',
            borderRadius: 8,
            color: 'var(--danger)',
            fontSize: 13,
          }}>
             {apiError}
          </div>
        )}

        {/* Action Buttons */}
        <div className="flex gap-12 mt-16">
          <button
            className="btn btn-primary btn-lg"
            onClick={handleAnalyze}
            disabled={!file || loading}
            style={{ flex: 1 }}
          >
            {loading ? (
              <><div className="spinner sm" /> Processing...</>
            ) : (
              ' Analyze Transactions'
            )}
          </button>
          {file && !loading && (
            <button className="btn btn-outline" onClick={() => { setFile(null); setResults(null); }}>
               Clear
            </button>
          )}
        </div>

        {/* CSV Format Instructions */}
        <div className="csv-instructions mt-16">
          <p style={{ fontWeight: 600, color: 'var(--text-secondary)', marginBottom: 8 }}>
             Expected CSV Format:
          </p>
          <code>Time, V1, V2, V3, ... V28, Amount</code>
          <p style={{ marginTop: 6 }}>
            Each row represents one transaction. The model uses the same features as the
            <strong style={{ color: 'var(--accent-cyan)' }}> Kaggle Credit Card Fraud Detection</strong> dataset.
          </p>
        </div>
      </Card>

      {/* ── Results ── */}
      {results && stats && (
        <div>
          {/* Summary Stats */}
          <div className="stats-grid mb-20">
            <StatCard title="Total Analyzed"  value={stats.total} icon="" color="blue"   subtitle="Transactions in batch" />
            <StatCard title="Fraud Detected"  value={stats.fraud} icon="" color="red"    subtitle="Flagged as fraudulent" />
            <StatCard title="Legitimate"      value={stats.legit} icon="" color="green"  subtitle="Passed as legitimate" />
            <StatCard title="Fraud Rate"      value={stats.rate}  icon="" color="purple" subtitle="% of batch" suffix="%" />
          </div>

          <div className="charts-grid mb-20">
            {/* Results Table */}
            <Card
              title=" Batch Results"
              headerAction={
                <button
                  className="btn btn-ghost btn-sm"
                  onClick={() => downloadResultsCSV(results)}
                >
                  ⬇️ Download CSV
                </button>
              }
              noPadding
            >
              <DataTable
                columns={RESULT_COLUMNS.map((col, idx) =>
                  col.key === '_row'
                    ? { ...col, render: (val, row) => results.indexOf(row) + 1 }
                    : col
                )}
                data={results.slice(0, 100)} // Show first 100
                emptyMessage="No results"
              />
              {results.length > 100 && (
                <p style={{ padding: '12px 16px', fontSize: 12, color: 'var(--text-muted)' }}>
                  Showing first 100 of {results.length} rows. Download CSV for all results.
                </p>
              )}
            </Card>

            {/* Pie Chart */}
            <Card title="Fraud Distribution">
              <div style={{ height: 260 }}>
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={[
                        { name: 'Fraud',      value: stats.fraud },
                        { name: 'Legitimate', value: stats.legit },
                      ]}
                      cx="50%"
                      cy="50%"
                      innerRadius={55}
                      outerRadius={90}
                      paddingAngle={4}
                      dataKey="value"
                    >
                      <Cell fill="#ef4444" opacity={0.9} />
                      <Cell fill="#10b981" opacity={0.9} />
                    </Pie>
                    <Tooltip
                      contentStyle={{
                        background: 'rgba(17,24,39,0.95)',
                        border: '1px solid #1e2d45',
                        borderRadius: 8,
                        fontSize: 12,
                      }}
                    />
                    <Legend wrapperStyle={{ fontSize: 12, color: '#94a3b8' }} />
                  </PieChart>
                </ResponsiveContainer>
              </div>
              <div style={{ textAlign: 'center', marginTop: 4 }}>
                <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>
                  Fraud rate: <strong style={{ color: 'var(--danger)' }}>{stats.rate}%</strong>
                </span>
              </div>
            </Card>
          </div>
        </div>
      )}
    </div>
  );
}
