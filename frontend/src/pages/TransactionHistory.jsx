/**
 * TransactionHistory.jsx
 * Paginated, searchable, filterable history of all analyzed transactions.
 */

import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { useLocation } from 'react-router-dom';
import Card from '../components/UI/Card';
import DataTable from '../components/UI/DataTable';
import Badge from '../components/UI/Badge';
import EmptyState from '../components/UI/EmptyState';
import { getTransactionHistory, deleteTransactionHistory, deleteSingleTransaction } from '../services/api';
import { useToast } from '../components/UI/Toast';
import { useAuth } from '../context/AuthContext';

const PAGE_SIZE = 15;

// ── Fallback demo history ──────────────────────────────────────────────────────
const generateDemoHistory = () =>
  Array.from({ length: 42 }, (_, i) => {
    const isFraud = i % 7 === 0;
    const prob = isFraud
      ? 0.75 + Math.random() * 0.24
      : 0.01 + Math.random() * 0.35;
    return {
      transaction_id: `TXN-${String(10000 + i).padStart(6, '0')}`,
      date: new Date(Date.now() - i * 4800000).toLocaleString(),
      amount: (Math.random() * 8000 + 1).toFixed(2),
      prediction: isFraud ? 'fraud' : 'legitimate',
      fraud_probability: prob.toFixed(4),
      risk_level: prob > 0.7 ? 'high' : prob > 0.4 ? 'medium' : 'low',
    };
  });

// ── Table columns definition ───────────────────────────────────────────────────
const buildColumns = (onDelete) => [
  { key: 'transaction_id', label: 'Transaction ID', primary: true },
  { key: 'date',           label: 'Date / Time' },
  {
    key: 'amount',
    label: 'Amount',
    render: (val) => (
      <span style={{ color: 'var(--text-primary)', fontWeight: 600 }}>
        ₹{parseFloat(val).toFixed(2)}
      </span>
    ),
  },
  {
    key: 'prediction',
    label: 'Prediction',
    render: (val) => <Badge type={val} />,
  },
  {
    key: 'fraud_probability',
    label: 'Probability',
    render: (val) => {
      const pct = (parseFloat(val) * 100).toFixed(1);
      const color = parseFloat(pct) > 70 ? 'var(--danger)' : parseFloat(pct) > 40 ? 'var(--warning)' : 'var(--success)';
      return (
        <div className="prob-bar-wrap">
          <div className="prob-bar-track">
            <div className="prob-bar-fill" style={{ width: `${pct}%`, background: color }} />
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
  {
    key: 'actions',
    label: '',
    render: (_, row) => (
      <button 
        onClick={() => onDelete(row.transaction_id)}
        style={{ background: 'transparent', border: 'none', cursor: 'pointer', fontSize: '18px', padding: '4px', opacity: 0.6, transition: 'opacity 0.2s' }}
        onMouseEnter={(e) => e.target.style.opacity = 1}
        onMouseLeave={(e) => e.target.style.opacity = 0.6}
        title="Delete Transaction"
      >
        
      </button>
    )
  }
];

// ── Pagination Component ───────────────────────────────────────────────────────
function Pagination({ page, totalPages, onPageChange }) {
  if (totalPages <= 1) return null;

  const pages = [];
  const delta = 2;
  const range = [];

  for (let i = Math.max(1, page - delta); i <= Math.min(totalPages, page + delta); i++) {
    range.push(i);
  }

  if (range[0] > 1) {
    pages.push(1);
    if (range[0] > 2) pages.push('...');
  }
  pages.push(...range);
  if (range[range.length - 1] < totalPages) {
    if (range[range.length - 1] < totalPages - 1) pages.push('...');
    pages.push(totalPages);
  }

  return (
    <div className="pagination">
      <button
        className="page-btn"
        disabled={page === 1}
        onClick={() => onPageChange(page - 1)}
      >‹</button>
      {pages.map((p, i) =>
        p === '...' ? (
          <span key={`ellipsis-${i}`} style={{ padding: '0 4px', color: 'var(--text-muted)' }}>…</span>
        ) : (
          <button
            key={p}
            className={`page-btn ${p === page ? 'active' : ''}`}
            onClick={() => onPageChange(p)}
          >
            {p}
          </button>
        )
      )}
      <button
        className="page-btn"
        disabled={page === totalPages}
        onClick={() => onPageChange(page + 1)}
      >›</button>
    </div>
  );
}

// ── Main Component ─────────────────────────────────────────────────────────────
export default function TransactionHistory() {
  const toast = useToast();
  const { isAdmin } = useAuth();
  const location = useLocation();

  const [allData, setAllData]     = useState([]);
  const [loading, setLoading]     = useState(true);
  const [deleting, setDeleting]   = useState(false);
  const [page, setPage]           = useState(1);
  const [searchTerm, setSearch]   = useState('');
  const [filterPred, setFilterPred] = useState(location.state?.filterPred || 'all');    // all | fraud | legitimate
  const [filterRisk, setFilterRisk] = useState('all');    // all | high | medium | low
  const [isDemo, setIsDemo]       = useState(false);

  // ── Fetch Data ───────────────────────────────────────────────────────────────
  const fetchHistory = useCallback(async () => {
    setLoading(true);
    try {
      const data = await getTransactionHistory({ page_size: 500 });
      // Backend returns PaginatedTransactions with .items array
      // Each item has prediction as int (0=Legitimate, 1=Fraud)
      const rawRows = data?.items || data?.transactions || data?.data || data || [];
      const rows = Array.isArray(rawRows)
        ? rawRows.map((r) => ({
            ...r,
            // Normalize prediction int → string for Badge component
            prediction: r.prediction === 1 ? 'fraud' : 'legitimate',
            // Normalize date field (ensure UTC 'Z' is present for correct local conversion)
            date: r.created_at
              ? new Date(r.created_at.endsWith('Z') ? r.created_at : `${r.created_at}Z`).toLocaleString()
              : r.date || 'N/A',
            // Normalize risk_level to lowercase for Badge
            risk_level: (r.risk_level || 'low').toLowerCase(),
          }))
        : [];
      setAllData(rows);
      setIsDemo(false);
    } catch (err) {
      // Fall back to demo data
      setAllData(generateDemoHistory());
      setIsDemo(true);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchHistory();
  }, [fetchHistory]);

  // ── Filter + Search (client-side on demo data) ────────────────────────────────
  const filtered = useMemo(() => {
    let rows = allData;
    if (searchTerm) {
      const term = searchTerm.toLowerCase();
      rows = rows.filter((r) =>
        (r.transaction_id || '').toLowerCase().includes(term)
      );
    }
    if (filterPred !== 'all') {
      rows = rows.filter((r) => r.prediction === filterPred);
    }
    if (filterRisk !== 'all') {
      rows = rows.filter((r) => r.risk_level === filterRisk);
    }
    return rows;
  }, [allData, searchTerm, filterPred, filterRisk]);

  const totalPages = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE));
  const pageData   = filtered.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);

  // Reset to page 1 when filters change
  useEffect(() => { setPage(1); }, [searchTerm, filterPred, filterRisk]);

  // ── Clear History ────────────────────────────────────────────────────────────
  const handleClear = async () => {
    const confirmed = window.confirm(
      ' Are you sure you want to delete ALL transaction history?\nThis action cannot be undone.'
    );
    if (!confirmed) return;

    setDeleting(true);
    try {
      await deleteTransactionHistory();
      setAllData([]);
      toast.success('Transaction history cleared.', 'Deleted');
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to clear history.');
    } finally {
      setDeleting(false);
    }
  };

  const handleDeleteSingle = async (transactionId) => {
    const confirmed = window.confirm('Are you sure you want to delete this transaction?');
    if (!confirmed) return;
    
    try {
      await deleteSingleTransaction(transactionId);
      setAllData(prev => prev.filter(t => t.transaction_id !== transactionId));
      toast.success('Transaction deleted successfully.');
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to delete transaction.');
    }
  };

  const columns = buildColumns(handleDeleteSingle);

  return (
    <div>
      {/* ── Demo Banner ── */}
      {isDemo && (
        <div className="demo-banner">
          <span></span>
          <span><strong>Demo Mode</strong> — Showing sample transaction history. Connect backend to see real data.</span>
        </div>
      )}

      <Card
        title=" Transaction History"
        headerAction={
          <div className="flex gap-8">
            <button className="btn btn-outline btn-sm" onClick={fetchHistory} disabled={loading}>
               Refresh
            </button>
            <button className="btn btn-danger btn-sm" onClick={handleClear} disabled={deleting || allData.length === 0}>{deleting ? 'Clearing...' : '??? Clear History'}</button>
          </div>
        }
        noPadding
      >
        {/* ── Filters ── */}
        <div style={{ padding: '16px 20px', borderBottom: '1px solid var(--border)' }}>
          <div className="filters-row">
            {/* Search */}
            <div className="search-bar">
              <span className="search-icon"></span>
              <input
                type="text"
                placeholder="Search by Transaction ID..."
                value={searchTerm}
                onChange={(e) => setSearch(e.target.value)}
              />
            </div>

            {/* Prediction Filter */}
            <select
              className="form-input"
              style={{ width: 'auto', paddingRight: 36 }}
              value={filterPred}
              onChange={(e) => setFilterPred(e.target.value)}
            >
              <option value="all">All Predictions</option>
              <option value="fraud">Fraud Only</option>
              <option value="legitimate">Legitimate Only</option>
            </select>

            {/* Risk Filter */}
            <select
              className="form-input"
              style={{ width: 'auto', paddingRight: 36 }}
              value={filterRisk}
              onChange={(e) => setFilterRisk(e.target.value)}
            >
              <option value="all">All Risk Levels</option>
              <option value="high">High Risk</option>
              <option value="medium">Medium Risk</option>
              <option value="low">Low Risk</option>
            </select>

            {/* Count Display */}
            <span style={{ marginLeft: 'auto', fontSize: 12, color: 'var(--text-muted)' }}>
              Showing <strong style={{ color: 'var(--text-primary)' }}>{pageData.length}</strong> of{' '}
              <strong style={{ color: 'var(--text-primary)' }}>{filtered.length}</strong> transactions
            </span>
          </div>
        </div>

        {/* ── Table ── */}
        <DataTable
          columns={columns}
          data={pageData}
          loading={loading}
          emptyMessage={allData.length === 0 ? 'No transaction history yet' : 'No results match your filters'}
          emptyIcon={allData.length === 0 ? '📭' : ''}
          emptyDescription={
            allData.length === 0
              ? 'Analyze a transaction or run a batch job to see results here.'
              : 'Try adjusting the search term or filters.'
          }
        />

        {/* ── Pagination ── */}
        {!loading && filtered.length > PAGE_SIZE && (
          <Pagination page={page} totalPages={totalPages} onPageChange={setPage} />
        )}
      </Card>
    </div>
  );
}


