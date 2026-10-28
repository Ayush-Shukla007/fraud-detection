import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../components/UI/Toast';

export default function Login() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();
  const toast = useToast();

  const handleLogin = async (e, u, p) => {
    if (e) e.preventDefault();
    setLoading(true);
    try {
      await login(u || username, p || password);
      toast.success(`Successfully logged in as ${u || username}!`, 'Welcome');
      navigate('/');
    } catch (err) {
      toast.error('Invalid username or password', 'Login Failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ height: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'var(--bg-gradient)' }}>
      <div className="card" style={{ width: '400px', padding: '40px 32px' }}>
        <div style={{ textAlign: 'center', marginBottom: 32 }}>
          <div style={{ fontSize: 48, marginBottom: 12 }}></div>
          <h2 style={{ fontSize: 24, marginBottom: 8 }}>FraudGuard Pro</h2>
          <p style={{ color: 'var(--text-muted)' }}>Sign in to your account</p>
        </div>
        
        <form onSubmit={handleLogin} style={{ display: 'flex', flexDirection: 'column', gap: 20, marginBottom: 24 }}>
          <div className="form-group">
            <label>Username</label>
            <input 
              type="text" 
              className="form-input" 
              value={username} 
              onChange={e => setUsername(e.target.value)} 
              placeholder="e.g. admin or viewer"
            />
          </div>
          <div className="form-group">
            <label>Password</label>
            <input 
              type="password" 
              className="form-input" 
              value={password} 
              onChange={e => setPassword(e.target.value)} 
              placeholder="••••••••"
            />
          </div>
          <button 
            type="submit" 
            className="btn btn-primary btn-full" 
            style={{ marginTop: 12 }}
            disabled={loading || !username || !password}
          >
            {loading ? 'Authenticating...' : 'Sign In'}
          </button>
        </form>

        <div style={{ borderTop: '1px solid var(--border)', paddingTop: 20 }}>
          <p style={{ textAlign: 'center', fontSize: 13, color: 'var(--text-muted)', marginBottom: 16 }}>Or use demo accounts:</p>
          <div style={{ display: 'flex', gap: 12 }}>
            <button 
              type="button"
              onClick={() => handleLogin(null, 'admin', 'admin')}
              className="btn btn-outline" 
              disabled={loading}
              style={{ flex: 1, padding: '10px', fontSize: '13px' }}
            >
              Admin Demo
            </button>
            <button 
              type="button"
              onClick={() => handleLogin(null, 'viewer', 'viewer')}
              className="btn btn-outline" 
              disabled={loading}
              style={{ flex: 1, padding: '10px', fontSize: '13px' }}
            >
              Viewer Demo
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
