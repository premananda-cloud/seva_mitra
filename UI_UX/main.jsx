import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import App from './App.jsx'
import './index.css'

// i18n must init before app renders
import './modules/language/i18n.js'

import { KeyboardProvider } from './context/KeyboardContext.jsx' // FIX: wrap app

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <BrowserRouter>
      <KeyboardProvider>
        <App />
      </KeyboardProvider>
    </BrowserRouter>
  </React.StrictMode>
)
