/**
 * api.js
 * Centralized API service layer for FraudGuard Pro.
 * All backend communication goes through this file.
 * Base URL is loaded from Vite environment variables.
 */

import axios from 'axios';

// ── Axios Instance ─────────────────────────────────────────────────────────────
const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000/api/v1',
  timeout: 30000, // 30 second timeout for batch requests
  headers: {
    'Content-Type': 'application/json',
  },
});

// ── Request Interceptor ────────────────────────────────────────────────────────
api.interceptors.request.use(
  (config) => {
    // Could add auth token here in the future
    return config;
  },
  (error) => Promise.reject(error)
);

// ── Response Interceptor ───────────────────────────────────────────────────────
api.interceptors.response.use(
  (response) => response,
  (error) => {
    // Normalize error messages for user-friendly display
    if (error.code === 'ERR_NETWORK' || error.code === 'ECONNREFUSED') {
      error.userMessage = 'Cannot connect to the server. Please ensure the backend is running on port 8000.';
    } else if (error.code === 'ECONNABORTED') {
      error.userMessage = 'Request timed out. The server may be overloaded.';
    } else if (error.response?.status === 422) {
      error.userMessage = 'Invalid data format. Please check your inputs.';
    } else if (error.response?.status === 500) {
      error.userMessage = 'Server error. Please try again later.';
    } else if (error.response?.data?.detail) {
      error.userMessage = error.response.data.detail;
    } else {
      error.userMessage = error.message || 'An unexpected error occurred.';
    }
    return Promise.reject(error);
  }
);

// ── API Functions ──────────────────────────────────────────────────────────────

/**
 * Analyze a single transaction for fraud.
 * @param {Object} data - Transaction feature data (Amount, Time, V1-V28)
 * @returns {Promise<Object>} Prediction result
 */
export const analyzeSingleTransaction = async (data) => {
  const response = await api.post('/predict', data);
  return response.data;
};

/**
 * Analyze a batch of transactions from a CSV file.
 * @param {FormData} formData - FormData containing the CSV file
 * @returns {Promise<Object>} Batch prediction results
 */
export const analyzeBatchTransactions = async (formData) => {
  const response = await api.post('/predict/batch', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 60000, // Extended timeout for batch processing
  });
  return response.data;
};

/**
 * Retrieve transaction history with optional filters.
 * @param {Object} params - Query params (page, limit, filter, search)
 * @returns {Promise<Object>} Paginated transaction list
 */
export const getTransactionHistory = async (params = {}) => {
  const response = await api.get('/transactions', { params });
  return response.data;
};

/**
 * Delete all transaction history records.
 * Requires confirm=true query param as a backend safety guard.
 * @returns {Promise<Object>} Confirmation response
 */
export const deleteTransactionHistory = async () => {
  const response = await api.delete('/transactions', { params: { confirm: true } });
  return response.data;
};

/**
 * Delete a single transaction.
 * @param {string} transactionId - The UUID of the transaction to delete
 * @returns {Promise<Object>} Confirmation response
 */
export const deleteSingleTransaction = async (transactionId) => {
  const response = await api.delete(`/transactions/${transactionId}`);
  return response.data;
};

/**
 * Get dashboard statistics (total, fraud count, rates, etc.)
 * @returns {Promise<Object>} Dashboard stats object
 */
export const getDashboardStats = async () => {
  const response = await api.get('/dashboard/stats');
  return response.data;
};

/**
 * Get time-series chart data for the dashboard.
 * @returns {Promise<Object>} Chart data with daily counts
 */
export const getChartData = async () => {
  const response = await api.get('/dashboard/chart-data');
  return response.data;
};

/**
 * Get ML model performance metrics.
 * @returns {Promise<Object>} Metrics (accuracy, precision, recall, f1, roc_auc)
 */
export const getModelMetrics = async () => {
  const response = await api.get('/model/metrics');
  return response.data;
};

/**
 * Get health status of the backend API.
 * @returns {Promise<Object>} Health check response
 */
export const getHealthStatus = async () => {
  const response = await api.get('/health');
  return response.data;
};

export default api;
