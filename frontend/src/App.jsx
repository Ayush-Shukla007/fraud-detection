/**
 * App.jsx
 * Root application component.
 * Sets up React Router with nested layout routes and the Toast context.
 */

import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';

// Auth & Layout
import { AuthProvider, useAuth } from './context/AuthContext';
import ProtectedRoute from './components/Layout/ProtectedRoute';

// Page components
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import CheckTransaction from './pages/CheckTransaction';
import BatchDetection from './pages/BatchDetection';
import TransactionHistory from './pages/TransactionHistory';
import ModelPerformance from './pages/ModelPerformance';
import ApiIntegration from './pages/ApiIntegration';
import Settings from './pages/Settings';

// Toast notification system
import { ToastProvider } from './components/UI/Toast';

// Global styles
import './styles/globals.css';

// Redirect helper to skip login if already authenticated
const LoginRoute = () => {
  const { user } = useAuth();
  return user ? <Navigate to="/" replace /> : <Login />;
};

export default function App() {
  return (
    <ToastProvider>
      <AuthProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/login" element={<LoginRoute />} />
            
            {/* Protected Routes (All roles) */}
            <Route element={<ProtectedRoute />}>
              <Route index element={<Dashboard />} />
              <Route path="check" element={<CheckTransaction />} />
              <Route path="history" element={<TransactionHistory />} />
              <Route path="api-keys" element={<ApiIntegration />} />
              <Route path="settings" element={<Settings />} />
            </Route>

            {/* Admin-only Routes */}
            <Route element={<ProtectedRoute requireAdmin={true} />}>
              <Route path="batch" element={<BatchDetection />} />
              <Route path="performance" element={<ModelPerformance />} />
            </Route>
          </Routes>
        </BrowserRouter>
      </AuthProvider>
    </ToastProvider>
  );
}
