/**
 * Sidebar.jsx
 * Fixed left navigation sidebar with logo, nav items, and status indicator.
 */

import React from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';

const NAV_ITEMS = [
  { path: '/',            label: 'Dashboard',         icon: '', end: true },
  { path: '/check',       label: 'Check Transaction', icon: '' },
  { path: '/batch',       label: 'Batch Detection',   icon: '', adminOnly: true },
  { path: '/history',     label: 'History',           icon: '' },
  { path: '/api-keys',    label: 'Developer API',     icon: '' },
  { path: '/settings',    label: 'Settings',          icon: '' },
  { path: '/performance', label: 'Model Comparison',  icon: '', adminOnly: true },
];

export default function Sidebar() {
  const { user, isAdmin, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <aside className="sidebar">
      {/* ── Logo ── */}
      <div className="sidebar-logo">
        <span className="sidebar-logo-icon"></span>
        <span className="sidebar-logo-text">FraudGuard Pro</span>
      </div>

      {/* ── User Profile ── */}
      <div style={{ padding: '0 16px 16px', borderBottom: '1px solid var(--border)', marginBottom: 16 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <div style={{ width: 36, height: 36, borderRadius: '50%', background: 'var(--gradient-blue)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 'bold' }}>
            {user?.username?.[0]?.toUpperCase()}
          </div>
          <div style={{ flex: 1 }}>
            <div style={{ fontWeight: 600, fontSize: 13, textTransform: 'capitalize' }}>{user?.username}</div>
            <div style={{ fontSize: 11, color: isAdmin ? 'var(--accent-purple)' : 'var(--text-muted)' }}>
              {isAdmin ? 'Administrator' : 'Analyst Viewer'}
            </div>
          </div>
        </div>
      </div>

      {/* ── Navigation ── */}
      <nav className="sidebar-nav">
        <p className="sidebar-section-label">Navigation</p>

        {NAV_ITEMS.map((item) => {
          if (item.adminOnly && !isAdmin) return null;
          return (
            <NavLink
              key={item.path}
              to={item.path}
              end={item.end}
              className={({ isActive }) =>
                `sidebar-nav-item ${isActive ? 'active' : ''}`
              }
            >
              <span className="nav-icon">{item.icon}</span>
              <span className="nav-label">{item.label}</span>
            </NavLink>
          );
        })}
      </nav>

      {/* ── Footer Status ── */}
      <div className="sidebar-footer" style={{ marginTop: 'auto' }}>
        <button 
          onClick={handleLogout}
          className="btn btn-ghost btn-full" 
          style={{ marginBottom: 16, fontSize: 12, padding: '8px' }}
        >
          🚪 Sign Out
        </button>
        <div className="status-indicator">
          <div className="status-dot live" style={{ background: 'var(--success)' }} />
          <span className="status-text live" style={{ color: 'var(--success)', fontWeight: 600 }}>Live Mode</span>
        </div>
      </div>
    </aside>
  );
}

