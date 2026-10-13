/**
 * Badge.jsx
 * Semantic badge for transaction predictions and risk levels.
 * Handles both string types ('fraud'/'legitimate'/'high'/'medium'/'low')
 * and integer prediction values (0=Legitimate, 1=Fraud) from the backend.
 */

import React from 'react';

const BADGE_CONFIG = {
  fraud:      { label: 'Fraud',       className: 'fraud' },
  legitimate: { label: 'Legitimate',  className: 'legitimate' },
  high:       { label: 'High Risk',   className: 'high' },
  medium:     { label: 'Medium Risk', className: 'medium' },
  low:        { label: 'Low Risk',    className: 'low' },
};

/**
 * @param {'fraud'|'legitimate'|'high'|'medium'|'low'|0|1} type - Badge type
 * @param {string} label - Override the default label text
 */
export default function Badge({ type, label }) {
  // Normalize integer prediction values from backend
  let normalizedType = type;
  if (type === 1) normalizedType = 'fraud';
  else if (type === 0) normalizedType = 'legitimate';
  else if (typeof type === 'string') normalizedType = type.toLowerCase();

  const config = BADGE_CONFIG[normalizedType] || BADGE_CONFIG.low;
  return (
    <span className={`badge ${config.className}`}>
      <span className="badge-dot" />
      {label || config.label}
    </span>
  );
}
