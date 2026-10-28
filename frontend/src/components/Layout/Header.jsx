/**
 * Header.jsx
 * Fixed top header bar with dynamic page title and live clock.
 */

import React, { useState, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import { ShieldCheck } from 'lucide-react';

// ── Route title + subtitle map ─────────────────────────────────────────────────
const ROUTE_META = {
  '/':            { title: 'Dashboard',          subtitle: 'Overview of fraud detection activity' },
  '/check':       { title: 'Check Transaction',   subtitle: 'Analyze a single transaction for fraud' },
  '/batch':       { title: 'Batch Detection',     subtitle: 'Upload and analyze multiple transactions at once' },
  '/history':     { title: 'Transaction History', subtitle: 'Browse past predictions and results' },
  '/performance': { title: 'Model Comparison',    subtitle: 'ML model metrics and performance benchmarks' },
  '/api-keys':    { title: 'Developer API',      subtitle: 'API documentation and credentials' },
  '/settings':    { title: 'Settings',          subtitle: 'Manage profile preferences and history' },
};

export default function Header() {
  const location = useLocation();
  const meta = ROUTE_META[location.pathname] || { title: 'FraudGuard Pro', subtitle: '' };

  // ── Live clock ──────────────────────────────────────────────────────────────
  const [time, setTime] = useState(new Date());

  useEffect(() => {
    const interval = setInterval(() => setTime(new Date()), 1000);
    return () => clearInterval(interval);
  }, []);

  const formatTime = (d) =>
    d.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', second: '2-digit' });

  const formatDate = (d) =>
    d.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric', year: 'numeric' });

  return (
    <header className="header">
      {/* Left: Page Title */}
      <div>
        <h1 className="header-title">{meta.title}</h1>
        {meta.subtitle && <p className="header-subtitle">{meta.subtitle}</p>}
      </div>

      {/* Right: Clock + Shield */}
      <div className="header-right">
        <div className="header-time">
          <div className="header-time-value">{formatTime(time)}</div>
          <div className="header-time-date">{formatDate(time)}</div>
        </div>
        <div className="header-shield" title="System Protected" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <ShieldCheck size={20} color="var(--success)" />
        </div>
      </div>
    </header>
  );
}
