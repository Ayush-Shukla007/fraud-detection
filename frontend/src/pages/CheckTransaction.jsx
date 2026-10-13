/**
 * CheckTransaction.jsx
 * Single transaction fraud analysis form with animated result display.
 * Supports all 30 features: Time, Amount, V1–V28.
 */

import React, { useState, useCallback } from 'react';
import Card from '../components/UI/Card';
import Badge from '../components/UI/Badge';
import { analyzeSingleTransaction } from '../services/api';
import { useToast } from '../components/UI/Toast';

// ── Feature definitions V1–V28 ─────────────────────────────────────────────────
const V_FEATURES = Array.from({ length: 28 }, (_, i) => ({
  name: `V${i + 1}`,
  placeholder: (Math.random() * 4 - 2).toFixed(4),
}));

// ── Probability Gauge SVG ──────────────────────────────────────────────────────
function ProbabilityGauge({ probability }) {
  const radius = 50;
  const circumference = 2 * Math.PI * radius;
  const pct = Math.min(Math.max(probability * 100, 0), 100);
  const offset = circumference - (pct / 100) * circumference;

  const color = pct >= 70 ? '#ef4444' : pct >= 40 ? '#f59e0b' : '#10b981';

  return (
    <div className="gauge-wrap">
      <div className="gauge-circle">
        <svg className="gauge-svg" width="120" height="120" viewBox="0 0 120 120">
          <circle className="gauge-track" cx="60" cy="60" r={radius} />
          <circle
            className="gauge-fill"
            cx="60"
            cy="60"
            r={radius}
            stroke={color}
            strokeDasharray={circumference}
            strokeDashoffset={offset}
            style={{ filter: `drop-shadow(0 0 6px ${color})` }}
          />
        </svg>
        <div className="gauge-label">
          <span className="gauge-percent" style={{ color }}>
            {pct.toFixed(1)}%
          </span>
          <span className="gauge-sub">Probability</span>
        </div>
      </div>
    </div>
  );
}

// ── Result Display ─────────────────────────────────────────────────────────────
function ResultCard({ result }) {
  const probability = result.fraud_probability ?? result.probability ?? 0;
  
  // Use existing probability to determine risk category using default threshold if backend doesn't provide it
  // Assuming default HIGH threshold is 0.80 and MEDIUM is 0.30 as seen in typical setups, 
  // but if result.risk_level exists, rely on that first.
  let riskLevel = (result.risk_level || '').toLowerCase();
  if (!riskLevel) {
    if (probability >= 0.80) riskLevel = 'high';
    else if (probability >= 0.30) riskLevel = 'medium';
    else riskLevel = 'low';
  }

  const probPct = (probability * 100).toFixed(0) + '%';
  const amtFormatted = result.amount ? `₹${parseFloat(result.amount).toLocaleString('en-IN')}` : 'N/A';

  if (riskLevel === 'high') {
    return (
      <div className="result-card fraud" style={{ animation: 'fadeInUp 0.3s ease', background: 'rgba(239,68,68,0.1)', border: '2px solid var(--danger)' }}>
        <h3 style={{ fontSize: 24, marginBottom: 16, color: 'var(--danger)', fontWeight: 'bold' }}>
           HIGH RISK TRANSACTION DETECTED
        </h3>
        <p style={{ fontSize: 16, marginBottom: 8 }}>Transaction Amount: <strong>{amtFormatted}</strong></p>
        <p style={{ fontSize: 16, marginBottom: 24 }}>Fraud Probability: <strong>{probPct}</strong></p>
        <div style={{ background: 'rgba(239,68,68,0.2)', padding: '16px', borderRadius: '8px', borderLeft: '4px solid var(--danger)' }}>
          <p style={{ margin: 0, fontWeight: 500 }}> This transaction has been flagged as suspicious.</p>
          <p style={{ margin: 0, fontWeight: 500 }}>Please verify the transaction before proceeding.</p>
        </div>
      </div>
    );
  }

  if (riskLevel === 'medium') {
    return (
      <div className="result-card" style={{ animation: 'fadeInUp 0.3s ease', background: 'rgba(245,158,11,0.1)', border: '2px solid var(--warning)' }}>
        <h3 style={{ fontSize: 20, marginBottom: 16, color: 'var(--warning)', fontWeight: 'bold' }}>
           Transaction requires attention
        </h3>
        <p style={{ fontSize: 16, marginBottom: 8 }}>Transaction Amount: <strong>{amtFormatted}</strong></p>
        <p style={{ fontSize: 16, margin: 0 }}>Fraud Probability: <strong>{probPct}</strong></p>
      </div>
    );
  }

  return (
    <div className="result-card legitimate" style={{ animation: 'fadeInUp 0.3s ease', background: 'rgba(16,185,129,0.1)', border: '2px solid var(--success)' }}>
      <h3 style={{ fontSize: 20, marginBottom: 16, color: 'var(--success)', fontWeight: 'bold' }}>
         Transaction appears safe
      </h3>
      <p style={{ fontSize: 16, marginBottom: 8 }}>Transaction Amount: <strong>{amtFormatted}</strong></p>
      <p style={{ fontSize: 16, margin: 0 }}>Fraud Probability: <strong>{probPct}</strong></p>
    </div>
  );
}

// ── Feature Input ──────────────────────────────────────────────────────────────
function FeatureInput({ name, value, onChange, error }) {
  return (
    <div className="form-group">
      <label className="form-label">{name}</label>
      <input
        type="number"
        step="any"
        className={`form-input ${error ? 'error' : ''}`}
        placeholder="0.0000"
        value={value}
        onChange={(e) => onChange(name, e.target.value)}
      />
    </div>
  );
}

// ── Main Component ─────────────────────────────────────────────────────────────
export default function CheckTransaction() {
  const toast = useToast();

  // Build initial form state: Time + Amount + V1–V28
  const initialForm = {
    Time: '',
    Amount: '',
    ...Object.fromEntries(V_FEATURES.map((f) => [f.name, ''])),
  };

  const [form, setForm]               = useState(initialForm);
  const [errors, setErrors]           = useState({});
  const [loading, setLoading]         = useState(false);
  const [result, setResult]           = useState(null);
  const [apiError, setApiError]       = useState(null);
  const [showAdvanced, setShowAdvanced] = useState(false);

  // ── Handle Input Change ──────────────────────────────────────────────────────
  const handleChange = useCallback((name, value) => {
    setForm((prev) => ({ ...prev, [name]: value }));
    if (errors[name]) {
      setErrors((prev) => ({ ...prev, [name]: '' }));
    }
  }, [errors]);

  // ── Validation ────────────────────────────────────────────────────────────────
  const validate = () => {
    const newErrors = {};
    if (form.Amount === '' || isNaN(parseFloat(form.Amount))) {
      newErrors.Amount = 'Amount is required and must be a number';
    } else if (parseFloat(form.Amount) < 0) {
      newErrors.Amount = 'Amount cannot be negative';
    }
    if (form.Time === '' || isNaN(parseFloat(form.Time))) {
      newErrors.Time = 'Time is required and must be a number (seconds elapsed)';
    }
    // V1–V14 required
    for (let i = 1; i <= 14; i++) {
      const key = `V${i}`;
      if (form[key] === '' || isNaN(parseFloat(form[key]))) {
        newErrors[key] = `${key} is required`;
      }
    }
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  // ── Submit ────────────────────────────────────────────────────────────────────
  const handleSubmit = async (e) => {
    e.preventDefault();
    setResult(null);
    setApiError(null);

    if (!validate()) {
      toast.error('Please fix the form errors before submitting.');
      return;
    }

    // Convert all values to floats and keys to lowercase (API expects amount, time, v1, etc.)
    const payload = {};
    Object.entries(form).forEach(([k, v]) => {
      payload[k.toLowerCase()] = parseFloat(v) || 0;
    });

    setLoading(true);
    try {
      const data = await analyzeSingleTransaction(payload);
      setResult(data);
      const isFraud = data.prediction === 'fraud' || data.prediction === 1;
      if (isFraud) {
        toast.error(' Fraudulent transaction detected!', 'Fraud Alert');
      } else {
        toast.success('Transaction appears legitimate.', 'Analysis Complete');
      }
    } catch (err) {
      setApiError(err.userMessage || 'Failed to analyze transaction.');
      toast.error(err.userMessage || 'API Error', 'Analysis Failed');
    } finally {
      setLoading(false);
    }
  };

  // ── Fill with sample data ─────────────────────────────────────────────────────
  const fillSample = (type = 'legitimate') => {
    const sample = type === 'fraud'
      ? {
          Time: '165704', Amount: '59333.76',
          V1: '-5.272272', V2: '-2.194733', V3: '-1.205379',
          V4: '2.009346', V5: '-3.666843', V6: '3.727464',
          V7: '-4.565889', V8: '-1.1181', V9: '-1.898468',
          V10: '-0.320246', V11: '5.911381', V12: '-1.169255',
          V13: '-1.640489', V14: '-3.154945',
          V15: '1.319255', V16: '-1.161015', V17: '1.326705',
          V18: '-0.094108', V19: '2.419501', V20: '0.23151',
          V21: '0.916129', V22: '2.386235', V23: '-0.180987',
          V24: '0.108674', V25: '1.211382', V26: '-0.575139',
          V27: '1.345653', V28: '0.111284',
        }
      : {
          Time: '0', Amount: '14363.52',
          V1: '-1.3598071336738', V2: '-0.0727811733098497', V3: '2.53634673796914',
          V4: '1.37815522427443', V5: '-0.338320769942518', V6: '0.462387777762292',
          V7: '0.239598554061257', V8: '0.0986979012610507', V9: '0.363786969611213',
          V10: '0.0907941719789316', V11: '-0.551599533260813', V12: '-0.617800855762348',
          V13: '-0.991389847235408', V14: '-0.311169353699879',
          V15: '1.46817697209427', V16: '-0.470400525259478', V17: '0.207971241929242',
          V18: '0.0257905801985591', V19: '0.403992960255733', V20: '0.251412098239705',
          V21: '-0.018306777944153', V22: '0.277837575558899', V23: '-0.110473910188767',
          V24: '0.0669280749146731', V25: '0.128539358273528', V26: '-0.189114843888824',
          V27: '0.133558376740387', V28: '-0.0210530534538215',
        };
    setForm({ ...initialForm, ...sample });
    setErrors({});
    toast.info(`Sample ${type} transaction loaded.`, 'Sample Data');
  };

  return (
    <div>
      {/* ── Info Banner ── */}
      <div className="info-banner mb-20">
        <span className="info-banner-icon">ℹ️</span>
        <span>
          <strong>V1–V28</strong> are PCA-transformed features derived from the original credit card dataset to protect cardholder privacy.
          Enter known values or use the sample buttons to test the model.
        </span>
      </div>

      <div className="grid-2" style={{ gap: 24 }}>
        {/* ── Form ── */}
        <div>
          <Card title=" Transaction Features">
            <form onSubmit={handleSubmit}>
              {/* Primary Fields */}
              <div style={{ marginBottom: 20 }}>
                <p style={{ fontSize: 11, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.8px', fontWeight: 600, marginBottom: 12 }}>
                  Primary Fields
                </p>
                <div className="grid-2" style={{ gap: 14 }}>
                  <div className="form-group">
                    <label className="form-label">
                      Amount (₹) <span className="required">*</span>
                    </label>
                    <input
                      type="number"
                      step="0.01"
                      min="0"
                      className={`form-input ${errors.Amount ? 'error' : ''}`}
                      placeholder="e.g. 149.62"
                      value={form.Amount}
                      onChange={(e) => handleChange('Amount', e.target.value)}
                    />
                    {errors.Amount && <span className="form-error">{errors.Amount}</span>}
                  </div>
                  <div className="form-group">
                    <label className="form-label">
                      Time (seconds) <span className="required">*</span>
                    </label>
                    <input
                      type="number"
                      step="1"
                      min="0"
                      className={`form-input ${errors.Time ? 'error' : ''}`}
                      placeholder="e.g. 0"
                      value={form.Time}
                      onChange={(e) => handleChange('Time', e.target.value)}
                    />
                    {errors.Time && <span className="form-error">{errors.Time}</span>}
                    <span className="form-hint">Seconds elapsed from first transaction</span>
                  </div>
                </div>
              </div>

              {/* V1 – V14 */}
              <div style={{ marginBottom: 16 }}>
                <p style={{ fontSize: 11, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.8px', fontWeight: 600, marginBottom: 12 }}>
                  PCA Features V1 – V14 <span className="required">*</span>
                </p>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 10 }}>
                  {V_FEATURES.slice(0, 14).map((f) => (
                    <FeatureInput
                      key={f.name}
                      name={f.name}
                      value={form[f.name]}
                      onChange={handleChange}
                      error={errors[f.name]}
                    />
                  ))}
                </div>
              </div>

              {/* V15 – V28 (Collapsible) */}
              <div style={{ marginBottom: 24 }}>
                <button
                  type="button"
                  className="section-toggle"
                  onClick={() => setShowAdvanced((v) => !v)}
                >
                  {showAdvanced ? '▲' : '▼'} {showAdvanced ? 'Hide' : 'Show'} Advanced Features (V15–V28)
                </button>
                <div className={`collapsible-content ${showAdvanced ? 'open' : 'closed'}`}>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 10, paddingTop: 12 }}>
                    {V_FEATURES.slice(14, 28).map((f) => (
                      <FeatureInput
                        key={f.name}
                        name={f.name}
                        value={form[f.name]}
                        onChange={handleChange}
                        error={errors[f.name]}
                      />
                    ))}
                  </div>
                </div>
              </div>

              {/* Sample Buttons */}
              <div className="flex gap-8 mb-16">
                <button type="button" className="btn btn-outline btn-sm" onClick={() => fillSample('legitimate')}>
                  📥 Load Legitimate Sample
                </button>
                <button type="button" className="btn btn-outline btn-sm" onClick={() => fillSample('fraud')}>
                  📥 Load Fraud Sample
                </button>
                <button type="button" className="btn btn-outline btn-sm" onClick={() => { setForm(initialForm); setErrors({}); setResult(null); }}>
                   Clear
                </button>
              </div>

              {/* Submit */}
              <button
                type="submit"
                disabled={loading}
                className="btn btn-primary btn-lg btn-full"
              >
                {loading ? (
                  <>
                    <div className="spinner sm" />
                    Analyzing Transaction...
                  </>
                ) : (
                  <> Analyze Transaction</>
                )}
              </button>

              {/* API Error */}
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
            </form>
          </Card>
        </div>

        {/* ── Result Panel ── */}
        <div>
          {/* Help Card */}
          <Card title="📖 How It Works" className="mb-16" style={{ marginBottom: 20 }}>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
              {[
                { icon: '1️⃣', title: 'Enter Features', desc: 'Fill in the transaction amount, time, and PCA-transformed V1–V28 features.' },
                { icon: '2️⃣', title: 'Analyze',        desc: 'The ML model (trained on 284,807 real transactions) scores the transaction.' },
                { icon: '3️⃣', title: 'Review Result',  desc: 'View the prediction, fraud probability, and risk level assessment.' },
              ].map((step) => (
                <div key={step.icon} className="flex gap-12">
                  <span style={{ fontSize: 18, flexShrink: 0 }}>{step.icon}</span>
                  <div>
                    <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)', marginBottom: 2 }}>{step.title}</div>
                    <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>{step.desc}</div>
                  </div>
                </div>
              ))}
            </div>
          </Card>

          {/* Risk Legend */}
          <Card title="🎨 Risk Level Legend">
            <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
              {[
                { level: 'high',   pct: '>70%',  desc: 'Very likely fraud. Immediate review.' },
                { level: 'medium', pct: '40–70%', desc: 'Suspicious. Requires manual check.' },
                { level: 'low',    pct: '<40%',   desc: 'Likely legitimate. Low risk.' },
              ].map((item) => (
                <div key={item.level} className="flex gap-12" style={{ alignItems: 'center' }}>
                  <Badge type={item.level} />
                  <div>
                    <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>
                      {item.pct} — {item.desc}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </Card>
        </div>
      </div>

      {/* ── Result Card ── */}
      {result && <ResultCard result={result} />}
    </div>
  );
}
