/**
 * Toast.jsx
 * Global toast notification system using React Context.
 * Usage: wrap app with <ToastProvider>, then call useToast() hook anywhere.
 */

import React, { createContext, useContext, useState, useCallback } from 'react';
import { CheckCircle, AlertCircle, Info, AlertTriangle } from 'lucide-react';

// ── Context ────────────────────────────────────────────────────────────────────
const ToastContext = createContext(null);

let toastIdCounter = 0;

// ── Provider ───────────────────────────────────────────────────────────────────
export function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([]);

  /**
   * Add a new toast notification.
   * @param {string} message - The toast message
   * @param {string} type    - 'success' | 'error' | 'info' | 'warning'
   * @param {string} title   - Optional title
   * @param {number} duration - Auto-dismiss duration in ms (default 4000)
   */
  const addToast = useCallback((message, type = 'info', title = '', duration = 4000) => {
    const id = ++toastIdCounter;
    const toast = { id, message, type, title: title || getDefaultTitle(type) };

    setToasts((prev) => [...prev, toast]);

    // Auto-dismiss after duration
    setTimeout(() => {
      removeToast(id);
    }, duration);
  }, []);

  const removeToast = useCallback((id) => {
    // Mark as removing to trigger exit animation
    setToasts((prev) =>
      prev.map((t) => (t.id === id ? { ...t, removing: true } : t))
    );
    // Actually remove after animation completes
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 280);
  }, []);

  // Convenience helpers
  const toast = {
    success: (msg, title) => addToast(msg, 'success', title),
    error:   (msg, title) => addToast(msg, 'error',   title),
    info:    (msg, title) => addToast(msg, 'info',    title),
    warning: (msg, title) => addToast(msg, 'warning', title),
  };

  return (
    <ToastContext.Provider value={toast}>
      {children}
      <div className="toast-container">
        {toasts.map((t) => (
          <ToastItem key={t.id} toast={t} onClose={() => removeToast(t.id)} />
        ))}
      </div>
    </ToastContext.Provider>
  );
}

// ── Single Toast Item ──────────────────────────────────────────────────────────
function ToastItem({ toast, onClose }) {
  const icons = {
    success: <CheckCircle size={16} color="var(--success)" />,
    error:   <AlertCircle size={16} color="var(--danger)" />,
    info:    <Info size={16} color="var(--accent-blue)" />,
    warning: <AlertTriangle size={16} color="var(--warning)" />,
  };

  return (
    <div className={`toast ${toast.type} ${toast.removing ? 'removing' : ''}`}>
      <span className="toast-icon">{icons[toast.type]}</span>
      <div className="toast-body">
        {toast.title && <div className="toast-title">{toast.title}</div>}
        <div className="toast-message">{toast.message}</div>
      </div>
      <button className="toast-close" onClick={onClose} aria-label="Close">×</button>
    </div>
  );
}

// ── Hook ───────────────────────────────────────────────────────────────────────
export function useToast() {
  const ctx = useContext(ToastContext);
  if (!ctx) throw new Error('useToast must be used within a ToastProvider');
  return ctx;
}

/** Returns a sensible default title for each toast type */
function getDefaultTitle(type) {
  const titles = {
    success: 'Success',
    error:   'Error',
    info:    'Info',
    warning: 'Warning',
  };
  return titles[type] || '';
}
