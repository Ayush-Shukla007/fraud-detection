/**
 * EmptyState.jsx
 * Centered empty state placeholder with icon, title, and description.
 */

import React from 'react';

/**
 * @param {string} icon        - Emoji icon to display
 * @param {string} title       - Primary message
 * @param {string} description - Secondary helper text
 * @param {React.Node} action  - Optional action button/element
 */
export default function EmptyState({ icon = '', title = 'No data', description = '', action }) {
  return (
    <div className="empty-state">
      <div className="empty-state-icon">{icon}</div>
      <div className="empty-state-title">{title}</div>
      {description && <p className="empty-state-desc">{description}</p>}
      {action && <div style={{ marginTop: 20 }}>{action}</div>}
    </div>
  );
}
