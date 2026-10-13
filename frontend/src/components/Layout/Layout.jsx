/**
 * Layout.jsx
 * Root layout shell — combines Sidebar, Header, and the page outlet.
 */

import React from 'react';
import { Outlet, useLocation } from 'react-router-dom';
import Sidebar from './Sidebar';
import Header from './Header';

export default function Layout() {
  const location = useLocation();

  return (
    <div className="app-layout">
      {/* Fixed Left Sidebar */}
      <Sidebar />

      {/* Main Content Area (offset by sidebar width) */}
      <div className="main-content">
        {/* Fixed Top Header */}
        <Header />

        {/* Page Content — rendered by React Router's <Outlet> */}
        {/* key=location.pathname forces remount on route change, triggering CSS animations! */}
        <main className="page-content" key={location.pathname} style={{ animation: 'fadeInUp 0.4s ease-out forwards' }}>
          <Outlet />
        </main>
      </div>
    </div>
  );
}
