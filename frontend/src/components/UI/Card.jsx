/**
 * Card.jsx
 * Glassmorphism dark card — the base container for all dashboard sections.
 */

import React from 'react';

/**
 * @param {string}      title        - Optional card header title
 * @param {React.Node}  children     - Card body content
 * @param {string}      className    - Additional CSS class names
 * @param {React.Node}  headerAction - Optional action element in header (button, badge, etc.)
 * @param {boolean}     noPadding    - If true, removes default body padding
 */
export default function Card({ title, children, className = '', headerAction, noPadding = false }) {
  return (
    <div className={`card ${className}`}>
      {title && (
        <div className="card-header">
          <h3 className="card-title">{title}</h3>
          {headerAction && <div>{headerAction}</div>}
        </div>
      )}
      <div className={`card-body ${noPadding ? 'no-padding' : ''}`}>
        {children}
      </div>
    </div>
  );
}
