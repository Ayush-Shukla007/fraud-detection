/**
 * EmptyState.jsx
 * Centered empty state placeholder with icon, title, and description.
 */

import React from 'react';
import { Inbox } from 'lucide-react';

/**
 * @param {React.Node} icon    - Icon to display
 * @param {string} title       - Primary message
 * @param {string} description - Secondary helper text
 * @param {React.Node} action  - Optional action button/element
 */
export default function EmptyState({ icon, title = 'No data', description = '', action }) {
  return (
    <div className="empty-state">
      <div className="empty-state-icon" style={{ display: 'flex', justifyContent: 'center', marginBottom: 12 }}>
        {icon || <Inbox size={36} color="var(--text-muted)" />}
      </div>
      <div className="empty-state-title">{title}</div>
      {description && <p className="empty-state-desc">{description}</p>}
      {action && <div style={{ marginTop: 20 }}>{action}</div>}
    </div>
  );
}
