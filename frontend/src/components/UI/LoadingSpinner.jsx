/**
 * LoadingSpinner.jsx
 * Animated loading spinner with optional fullscreen overlay.
 */

import React from 'react';

/**
 * @param {boolean} fullscreen - If true, renders a dark overlay covering the whole screen
 * @param {string}  size       - 'sm' | 'md' (default: 'md')
 * @param {string}  text       - Optional text to display below the spinner
 */
export default function LoadingSpinner({ fullscreen = false, size = 'md', text = 'Loading...' }) {
  const spinnerEl = (
    <div className="spinner-wrap">
      <div className={`spinner ${size === 'sm' ? 'sm' : ''}`} />
      {text && size !== 'sm' && <p className="spinner-text">{text}</p>}
    </div>
  );

  if (fullscreen) {
    return (
      <div className="spinner-overlay">
        {spinnerEl}
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', justifyContent: 'center', padding: '40px 0' }}>
      {spinnerEl}
    </div>
  );
}
