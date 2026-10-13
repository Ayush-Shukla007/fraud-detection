/**
 * DataTable.jsx
 * Responsive, reusable table with loading skeleton and empty state.
 */

import React from 'react';
import LoadingSpinner from './LoadingSpinner';
import EmptyState from './EmptyState';

/**
 * @param {Array}   columns      - Array of { key, label, render? } objects
 * @param {Array}   data         - Array of data row objects
 * @param {boolean} loading      - Show loading spinner if true
 * @param {string}  emptyMessage - Message when data is empty
 * @param {string}  emptyIcon    - Icon for empty state
 */
export default function DataTable({
  columns = [],
  data = [],
  loading = false,
  emptyMessage = 'No data available',
  emptyIcon = '',
  emptyDescription = '',
}) {
  if (loading) {
    return <LoadingSpinner text="Loading data..." />;
  }

  if (!data || data.length === 0) {
    return (
      <EmptyState
        icon={emptyIcon}
        title={emptyMessage}
        description={emptyDescription}
      />
    );
  }

  return (
    <div className="table-wrap">
      <table className="data-table">
        <thead>
          <tr>
            {columns.map((col) => (
              <th key={col.key}>{col.label}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.map((row, rowIdx) => (
            <tr key={row.id || row.transaction_id || rowIdx}>
              {columns.map((col) => (
                <td
                  key={col.key}
                  className={col.primary ? 'primary' : ''}
                >
                  {col.render
                    ? col.render(row[col.key], row)
                    : row[col.key] ?? '—'}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
