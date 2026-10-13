import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { AreaChart, Area, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import Card from '../components/UI/Card';
import StatCard from '../components/UI/StatCard';
import DataTable from '../components/UI/DataTable';
import Badge from '../components/UI/Badge';
import LoadingSpinner from '../components/UI/LoadingSpinner';
import { getDashboardStats, getChartData } from '../services/api';
import { useToast } from '../components/UI/Toast';
import { useAuth } from '../context/AuthContext';

const PIE_COLORS = ['#10b981', '#ef4444'];

const COLUMNS = [
  { key: 'transaction_id', label: 'ID', render: (val) => <span style={{ fontFamily: 'monospace', color: 'var(--text-muted)' }}>{val.slice(0, 8)}...</span> },
  { key: 'date', label: 'Date' },
  { key: 'amount', label: 'Amount', render: (val) => <span style={{ fontWeight: 600 }}>${val.toFixed(2)}</span> },
  { key: 'fraud_probability', label: 'Probability', render: (val) => (
      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
        <div style={{ flex: 1, height: 6, background: 'var(--bg-primary)', borderRadius: 3, overflow: 'hidden' }}>
          <div style={{ height: '100%', width: `${val * 100}%`, background: val > 0.5 ? 'var(--danger)' : 'var(--success)' }} />
        </div>
        <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>{Math.round(val * 100)}%</span>
      </div>
    )
  },
  { key: 'risk_level', label: 'Risk', render: (val) => <Badge type={val?.toLowerCase()} /> },
  { key: 'prediction', label: 'Status', render: (val) => <Badge type={val === 'fraud' ? 'fraud' : 'legitimate'} /> },
];

export default function Dashboard() {
  const toast = useToast();
  const navigate = useNavigate();
  const { user, isAdmin } = useAuth();
  
  const [stats, setStats] = useState(null);
  const [chartData, setChartData] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchData = useCallback(async () => {
    try {
      const [statsRes, chartRes] = await Promise.all([
        getDashboardStats(),
        getChartData()
      ]);
      setStats(statsRes);
      setChartData(chartRes.map(d => ({
        ...d,
        dateLabel: new Date(d.date).toLocaleDateString(undefined, { month: 'short', day: 'numeric' })
      })));
    } catch (err) {
      toast.error('Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  }, [toast]);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 30000);
    return () => clearInterval(interval);
  }, [fetchData]);

  if (loading) {
    return <div style={{ display: 'flex', justifyContent: 'center', marginTop: 100 }}><LoadingSpinner /></div>;
  }

  const pieData = stats ? [
    { name: 'Legitimate', value: stats.legitimate_transactions },
    { name: 'Fraud', value: stats.fraud_detected }
  ] : [];

  const tableData = stats?.recent_transactions?.map(r => ({
    ...r,
    prediction: r.prediction === 1 ? 'fraud' : 'legitimate',
    date: new Date(r.created_at).toLocaleString(),
  })) || [];

  return (
    <div>
      <div className="page-header" style={{ marginBottom: 32 }}>
        <h1 className="page-title"> Overview: {user?.username}</h1>
        <p className="page-subtitle">
          {isAdmin 
            ? "Overview of all transaction activity and system performance." 
            : "Test and monitor your own secure transactions."}
        </p>
      </div>

      {!isAdmin && stats?.fraud_detected > 0 && (
        <div style={{ background: 'rgba(239, 68, 68, 0.1)', border: '1px solid var(--danger)', borderRadius: 12, padding: 20, marginBottom: 32, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
            <span style={{ fontSize: 32 }}></span>
            <div>
              <h3 style={{ color: 'var(--danger)', margin: 0, marginBottom: 4, fontSize: 16 }}>Action Required: {stats.fraud_detected} Suspicious Transactions</h3>
              <p style={{ color: 'var(--text-primary)', margin: 0, fontSize: 14 }}>We blocked {stats.fraud_detected} potentially fraudulent attempts on your account. Please review them immediately.</p>
            </div>
          </div>
          <button className="btn btn-primary" onClick={() => navigate('/history', { state: { filterPred: 'fraud' } })} style={{ background: 'var(--danger)' }}>Review Now</button>
        </div>
      )}

      <div className="stats-grid mb-28">
        <StatCard 
          title={`Transactions`} 
          value={stats?.total_transactions || 0} 
          icon="" 
          color="blue" 
        />
        <StatCard 
          title="Fraud Detected" 
          value={stats?.fraud_detected || 0} 
          icon="" 
          color="red" 
        />
        <StatCard 
          title="Legitimate" 
          value={stats?.legitimate_transactions || 0} 
          icon="" 
          color="green" 
        />
        <StatCard 
          title="Fraud Rate" 
          value={`${stats?.fraud_rate || 0}%`} 
          icon="" 
          color="purple" 
        />
      </div>

      {!isAdmin && (
        <div className="charts-grid mb-28">
          <Card title=" Quick Analysis">
            <div style={{ display: 'flex', flexDirection: 'column', height: '100%', justifyContent: 'center' }}>
              <p style={{ color: 'var(--text-secondary)', marginBottom: 24, fontSize: 14, lineHeight: '1.6' }}>
                Run a manual risk analysis on a single transaction using the core FraudGuard Machine Learning engine.
              </p>
              <button className="btn btn-primary" onClick={() => navigate('/check')} style={{ width: '100%', padding: '16px 24px', fontSize: 16 }}>
                 Analyze New Transaction
              </button>
            </div>
          </Card>

          <Card title=" Risk Profile">
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '16px 0' }}>
              <div style={{ 
                width: 120, height: 120, borderRadius: '50%', 
                border: `8px solid ${stats?.fraud_detected > 0 ? 'var(--warning)' : 'var(--success)'}`,
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                flexDirection: 'column', marginBottom: 16,
                boxShadow: `0 0 20px ${stats?.fraud_detected > 0 ? 'rgba(245, 158, 11, 0.2)' : 'rgba(16, 185, 129, 0.2)'}`
              }}>
                <span style={{ fontSize: 36, fontWeight: 700, color: 'var(--text-primary)', lineHeight: 1 }}>
                  {stats?.fraud_detected > 0 ? (100 - stats.fraud_rate).toFixed(0) : '99'}
                </span>
                <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>/ 100</span>
              </div>
              <h3 style={{ margin: 0, color: stats?.fraud_detected > 0 ? 'var(--warning)' : 'var(--success)', fontSize: 18 }}>
                {stats?.fraud_detected > 0 ? 'Needs Attention' : 'Excellent Status'}
              </h3>
            </div>
          </Card>
        </div>
      )}

      <div className="charts-grid mb-28">
        <Card title={` Fraud Trend (30 Days)`}>
          <div className="chart-container" style={{ height: 350 }}>
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={chartData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                <defs>
                  <linearGradient id="colorFraud" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#ef4444" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#ef4444" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <XAxis dataKey="dateLabel" tick={{ fill: '#94a3b8', fontSize: 12 }} />
                <YAxis tick={{ fill: '#94a3b8', fontSize: 12 }} />
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
                <Tooltip 
                  contentStyle={{ background: 'rgba(17,24,39,0.9)', border: '1px solid var(--border)', borderRadius: 8 }}
                  itemStyle={{ color: '#f1f5f9' }}
                />
                <Area type="monotone" dataKey="fraud_count" stroke="#ef4444" fillOpacity={1} fill="url(#colorFraud)" name="Fraudulent" />
                <Area type="monotone" dataKey="legitimate_count" stroke="#10b981" fillOpacity={0} name="Legitimate" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </Card>

        <Card title={`🍩 Distribution`}>
          <div className="chart-container" style={{ height: 350, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={pieData}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={80}
                  paddingAngle={5}
                  dataKey="value"
                  stroke="none"
                  label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                >
                  {pieData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={PIE_COLORS[index % PIE_COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip 
                  contentStyle={{ background: 'rgba(17,24,39,0.9)', border: '1px solid var(--border)', borderRadius: 8 }}
                  itemStyle={{ color: '#f1f5f9' }}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </Card>
      </div>
    </div>
  );
}

