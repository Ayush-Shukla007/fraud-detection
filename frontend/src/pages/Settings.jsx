import React, { useState } from 'react';
import Card from '../components/UI/Card';
import { useToast } from '../components/UI/Toast';
import { deleteTransactionHistory } from '../services/api';

export default function Settings() {
  const toast = useToast();
  
  const [settings, setSettings] = useState({
    emailAlerts: true,
    autoBlock: false,
    twoFactor: true,
    strictEnforcement: false
  });

  const toggleSetting = (key) => {
    setSettings(prev => ({ ...prev, [key]: !prev[key] }));
    toast.success('Security preferences updated successfully.');
  };

  const ToggleItem = ({ id, title, description, isActive }) => (
    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '20px 0', borderBottom: '1px solid var(--border)' }}>
      <div style={{ paddingRight: 32 }}>
        <h3 style={{ color: 'var(--text-primary)', fontSize: 16, marginBottom: 4, fontWeight: 500 }}>{title}</h3>
        <p style={{ color: 'var(--text-secondary)', fontSize: 13, lineHeight: '1.4' }}>{description}</p>
      </div>
      <div>
        <button 
          onClick={() => toggleSetting(id)}
          style={{
            width: 44,
            height: 24,
            borderRadius: 12,
            background: isActive ? 'var(--accent-blue)' : 'rgba(255,255,255,0.1)',
            border: 'none',
            position: 'relative',
            cursor: 'pointer',
            transition: 'background 0.3s'
          }}
        >
          <div style={{
            width: 20,
            height: 20,
            background: '#fff',
            borderRadius: '50%',
            position: 'absolute',
            top: 2,
            left: isActive ? 22 : 2,
            transition: 'left 0.3s',
            boxShadow: '0 2px 4px rgba(0,0,0,0.2)'
          }} />
        </button>
      </div>
    </div>
  );

  return (
    <div>
      <div className="page-header" style={{ marginBottom: 32 }}>
        <h1 className="page-title"> Security Settings</h1>
        <p className="page-subtitle">Manage your account security and alert preferences.</p>
      </div>

      <Card title="Notifications & Alerts" className="mb-28">
        <ToggleItem 
          id="emailAlerts"
          title="Email Alerts for High-Risk Transactions"
          description="Receive an immediate email notification whenever the ML model flags a transaction with > 70% fraud probability."
          isActive={settings.emailAlerts}
        />
        <ToggleItem 
          id="autoBlock"
          title="Auto-Block Medium Risk"
          description="Automatically decline any transaction that exceeds 30% fraud probability, rather than just warning you."
          isActive={settings.autoBlock}
        />
      </Card>

      <Card title="Account Security">
        <ToggleItem 
          id="twoFactor"
          title="Two-Factor Authentication (2FA)"
          description="Require a one-time code from your authenticator app when logging in from unrecognized devices."
          isActive={settings.twoFactor}
        />
        <ToggleItem 
          id="strictEnforcement"
          title="Strict ML Enforcement"
          description="Enforce strict dataset matching. The ML model will flag extreme outliers regardless of transaction amount."
          isActive={settings.strictEnforcement}
        />
        
        <div style={{ marginTop: 24, padding: 16, background: 'rgba(239, 68, 68, 0.1)', borderRadius: 8, border: '1px solid rgba(239, 68, 68, 0.3)' }}>
          <h4 style={{ color: 'var(--danger)', margin: 0, marginBottom: 8 }}>Danger Zone</h4>
          <p style={{ color: 'var(--text-secondary)', fontSize: 13, marginBottom: 16 }}>Permanently delete all your transaction history. This action cannot be undone.</p>
          <button 
            className="btn btn-primary" 
            style={{ background: 'var(--danger)' }} 
            onClick={async () => {
              if (window.confirm('Are you absolutely sure you want to delete all transaction history?')) {
                try {
                  await deleteTransactionHistory();
                  toast.success('All transaction data has been permanently deleted.');
                } catch (err) {
                  toast.error(err.response?.data?.detail || 'Failed to delete history. (Are you an Admin?)');
                }
              }
            }}
          >
            Delete All Transaction Data
          </button>
        </div>
      </Card>
    </div>
  );
}
