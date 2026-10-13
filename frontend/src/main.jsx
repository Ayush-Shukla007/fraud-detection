/**
 * main.jsx
 * Application entry point — mounts the React 18 root.
 */

import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';

// Mount the app to the #root div in index.html
ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
