import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import App from './App.jsx';
import './index.css';
import { KeyboardProvider } from './context/KeyboardContext';
import './modules/language/i18n.js';

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <BrowserRouter>
      <KeyboardProvider>
        <App />
      </KeyboardProvider>
    </BrowserRouter>
  </React.StrictMode>
);