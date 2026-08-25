import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import App from './App';
import { FinOpsProvider } from './context/FinOpsContext';

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <FinOpsProvider>
      <App />
    </FinOpsProvider>
  </React.StrictMode>
);
