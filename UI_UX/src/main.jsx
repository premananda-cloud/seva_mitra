import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import App from './App.jsx'
import './index.css'

// i18n must init before app renders
import './modules/language/i18n.js'

import { KeyboardProvider } from './context/KeyboardContext.jsx'

const root = ReactDOM.createRoot(document.getElementById('root'))

root.render(
  <React.StrictMode>
    <BrowserRouter>
      <KeyboardProvider>
        <App />
      </KeyboardProvider>
    </BrowserRouter>
  </React.StrictMode>
)

// Dismiss the loading splash once React has painted its first frame
requestAnimationFrame(() => {
  requestAnimationFrame(() => {
    const splash = document.getElementById('app-splash')
    if (splash) splash.classList.add('hidden')
  })
})
