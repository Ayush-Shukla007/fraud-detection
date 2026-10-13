import React, { useState } from 'react';
import Card from '../components/UI/Card';

export default function ApiIntegration() {
  const [copied, setCopied] = useState(false);
  const apiKey = "fg_live_9a8b7c6d5e4f3g2h1i0j_mock_key";

  const copyToClipboard = () => {
    navigator.clipboard.writeText(apiKey);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const codeSnippets = {
    cURL: `curl -X POST https://api.fraudguard.ai/v1/predict \\
  -H "Authorization: Bearer ${apiKey}" \\
  -H "Content-Type: application/json" \\
  -d '{
    "amount": 150.00,
    "time": 0,
    "v1": -1.2,
    "v2": 0.5,
    "v3": 1.1
  }'`,
    Python: `import requests

url = "https://api.fraudguard.ai/v1/predict"
headers = {
    "Authorization": f"Bearer ${apiKey}",
    "Content-Type": "application/json"
}
data = {
    "amount": 150.00,
    "time": 0,
    "v1": -1.2,
    "v2": 0.5,
    "v3": 1.1
}

response = requests.post(url, json=data, headers=headers)
print(response.json())`,
    NodeJS: `const axios = require('axios');

const analyzeTransaction = async () => {
  try {
    const response = await axios.post('https://api.fraudguard.ai/v1/predict', {
      amount: 150.00,
      time: 0,
      v1: -1.2,
      v2: 0.5,
      v3: 1.1
    }, {
      headers: {
        'Authorization': \`Bearer ${apiKey}\`
      }
    });
    console.log(response.data);
  } catch (error) {
    console.error(error);
  }
};

analyzeTransaction();`
  };

  const [activeTab, setActiveTab] = useState('cURL');

  return (
    <div>
      <div className="page-header" style={{ marginBottom: 32 }}>
        <h1 className="page-title"> Developer API</h1>
        <p className="page-subtitle">Integrate the FraudGuard ML engine directly into your checkout flow.</p>
      </div>

      <Card title="Your Secret API Key" className="mb-28">
        <div style={{ display: 'flex', alignItems: 'center', gap: 16, marginTop: 16 }}>
          <div style={{ 
            flex: 1, 
            background: 'rgba(0,0,0,0.3)', 
            padding: '12px 16px', 
            borderRadius: 8, 
            border: '1px solid var(--border)',
            fontFamily: 'monospace',
            color: 'var(--text-primary)',
            fontSize: 16
          }}>
            {apiKey}
          </div>
          <button 
            onClick={copyToClipboard}
            className="btn btn-primary" 
            style={{ width: 100 }}
          >
            {copied ? "Copied!" : "Copy"}
          </button>
        </div>
        <p style={{ color: 'var(--warning)', marginTop: 16, fontSize: 13 }}>
           Keep this key secret. Do not expose it in client-side frontend code.
        </p>
      </Card>

      <Card title="Quick Start Snippets">
        <div style={{ display: 'flex', gap: 16, borderBottom: '1px solid var(--border)', marginBottom: 16, paddingBottom: 8 }}>
          {Object.keys(codeSnippets).map(lang => (
            <button 
              key={lang}
              onClick={() => setActiveTab(lang)}
              style={{
                background: 'none',
                border: 'none',
                color: activeTab === lang ? 'var(--accent-blue)' : 'var(--text-secondary)',
                fontWeight: activeTab === lang ? 600 : 400,
                cursor: 'pointer',
                fontSize: 15,
                padding: '4px 8px'
              }}
            >
              {lang}
            </button>
          ))}
        </div>
        <pre style={{ 
          background: 'rgba(0,0,0,0.3)', 
          padding: 24, 
          borderRadius: 8, 
          border: '1px solid var(--border)',
          overflowX: 'auto',
          color: 'var(--text-primary)',
          fontFamily: 'monospace',
          lineHeight: '1.5'
        }}>
          <code>
            {codeSnippets[activeTab]}
          </code>
        </pre>
      </Card>
    </div>
  );
}
