import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuthStore } from '@/modules/auth/authStore'
import { useEffect } from 'react'
import localDB from '/src/modules/localdb/localDB.js'

// Pages
import LanguageSelect from '@/modules/language/LanguageSelect'
import LoginPage      from '@/modules/auth/LoginPage'
import RegisterPage   from '@/modules/auth/RegisterPage'
import Dashboard      from '@/components/kiosk/Dashboard'
import ReceiptScreen  from '@/components/payment/ReceiptScreen'

// Orchestrator stub — real backend connection lives here later
import '@/modules/orchestrator/orchestrator'

// Protected route wrapper
function Protected({ children }) {
  const user = useAuthStore(s => s.user)
  if (!user) return <Navigate to="/login" replace />
  return children
}

// Public-only route (redirect away if already logged in)
function PublicOnly({ children }) {
  const user = useAuthStore(s => s.user)
  if (user) return <Navigate to="/dashboard" replace />
  return children
}

export default function App() {
  const initAuth = useAuthStore(s => s.initFromStorage)

  // On mount: boot the DB and rehydrate session
  useEffect(() => {
    localDB.init().then(() => initAuth())
  }, [initAuth])

  return (
    <Routes>
      {/* Language selection is always the first screen */}
      <Route path="/"         element={<LanguageSelect />} />

      {/* Auth routes — only for logged-out users */}
      <Route path="/login"    element={<PublicOnly><LoginPage /></PublicOnly>} />
      <Route path="/register" element={<PublicOnly><RegisterPage /></PublicOnly>} />

      {/* Protected app */}
      <Route path="/dashboard" element={<Protected><Dashboard /></Protected>} />

      {/* Receipt screen — shown after a successful payment */}
      <Route path="/receipt/:id" element={<Protected><ReceiptScreen /></Protected>} />

      {/* Fallback */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
