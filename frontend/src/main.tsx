import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App.tsx';
import './index.css';
import { installCmdkScrollFix } from './utils/cmdkScrollFix';

// Dark mode tokens loaded async — not needed for initial render
import('./dark-tokens.css');

// Wheel-Listener fuer cmdk Combobox-Scroll-Fix (#784).
installCmdkScrollFix();

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
