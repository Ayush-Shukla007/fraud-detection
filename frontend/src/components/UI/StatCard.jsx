/**
 * StatCard.jsx
 * KPI card with animated count-up number effect and color theming.
 */

import React, { useEffect, useRef, useState } from 'react';

/**
 * @param {string} title    - Metric label (e.g. "Total Transactions")
 * @param {string|number} value - The numeric or string value to display
 * @param {string} subtitle - Small text below value
 * @param {string} icon     - Emoji or icon character
 * @param {'blue'|'green'|'red'|'purple'} color - Color theme
 * @param {string} trend    - Optional trend text, e.g. "+12% this week"
 * @param {boolean} trendUp - If true, trend shows as red (fraud going up is bad)
 * @param {string} prefix   - Prefix before the value (e.g. "$")
 * @param {string} suffix   - Suffix after the value (e.g. "%")
 */
export default function StatCard({
  title,
  value,
  subtitle,
  icon = '',
  color = 'blue',
  trend,
  trendUp = false,
  prefix = '',
  suffix = '',
}) {
  const [displayValue, setDisplayValue] = useState(0);
  const animRef = useRef(null);
  const numericValue = parseFloat(String(value).replace(/[^0-9.]/g, ''));
  const isNumeric = !isNaN(numericValue);

  // Count-up animation on mount
  useEffect(() => {
    if (!isNumeric) return;
    const startTime = performance.now();
    const duration = 1200; // ms

    const step = (currentTime) => {
      const elapsed = currentTime - startTime;
      const progress = Math.min(elapsed / duration, 1);
      // Ease-out cubic
      const eased = 1 - Math.pow(1 - progress, 3);
      setDisplayValue(eased * numericValue);
      if (progress < 1) {
        animRef.current = requestAnimationFrame(step);
      }
    };

    animRef.current = requestAnimationFrame(step);
    return () => cancelAnimationFrame(animRef.current);
  }, [numericValue, isNumeric]);

  // Format the animated value to match original precision
  const formatValue = (val) => {
    const original = String(value);
    if (original.includes('.')) {
      const decimals = original.split('.')[1]?.length || 2;
      return val.toFixed(decimals);
    }
    return Math.round(val).toLocaleString();
  };

  const renderedValue = isNumeric ? formatValue(displayValue) : value;

  return (
    <div className={`stat-card ${color}`}>
      <div className="stat-card-header">
        <p className="stat-card-title">{title}</p>
        {icon && <div className={`stat-card-icon ${color}`}>{icon}</div>}
      </div>
      <div className={`stat-card-value ${color}`}>
        {prefix}{renderedValue}{suffix}
      </div>
      {subtitle && <p className="stat-card-subtitle">{subtitle}</p>}
      {trend && (
        <div className={`stat-card-trend ${trendUp ? 'up' : 'down'}`}>
          {trendUp ? '↑' : '↓'} {trend}
        </div>
      )}
    </div>
  );
}
