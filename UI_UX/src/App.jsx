import { Routes, Route, Navigate } from 'react-router-dom';
import { useAuthStore } from '@/modules/auth/authStore';
import { useEffect } from 'react';
import localDB from '@/modules/localdb/localDB.js';
import { useKeyboard } from './context/KeyboardContext';
import Keyboard from './components/kiosk/Keyboard';

// Pages
import LanguageSelect from '@/modules/language/LanguageSelect';
import LoginPage from '@/modules/auth/LoginPage';
import RegisterPage from '@/modules/auth/RegisterPage';
import Dashboard from '@/components/kiosk/Dashboard';
import ReceiptScreen   from '@/components/payment/ReceiptScreen';   // FIXED: was @/modules/payment/

// Department service screens
import ElectricityScreen  from '@/components/departments/ElectricityScreen';
import WaterScreen        from '@/components/departments/WaterScreen';
import MunicipalScreen    from '@/components/departments/MunicipalScreen';
import GasScreen          from '@/components/departments/GasScreen';
import ComplaintsScreen   from '@/components/departments/ComplaintsScreen';

// Orchestrator stub
import '@/modules/orchestrator/orchestrator';

// Protected route wrapper
function Protected({ children }) {
  const user = useAuthStore(s => s.user);
  if (!user) return <Navigate to="/login" replace />;
  return children;
}

// Public-only route (redirect away if already logged in)
function PublicOnly({ children }) {
  const user = useAuthStore(s => s.user);
  if (user) return <Navigate to="/dashboard" replace />;
  return children;
}

export default function App() {
  const initAuth = useAuthStore(s => s.initFromStorage);
  const { activeInput, handleKeyPress, blurInput } = useKeyboard();

  useEffect(() => {
    localDB.init().then(() => initAuth());
  }, [initAuth]);

  return (
    <>
      <Routes>
        <Route path="/"         element={<LanguageSelect />} />
        <Route path="/login"    element={<PublicOnly><LoginPage /></PublicOnly>} />
        <Route path="/register" element={<PublicOnly><RegisterPage /></PublicOnly>} />

        <Route path="/dashboard"             element={<Protected><Dashboard /></Protected>} />
        <Route path="/receipt/:id"           element={<Protected><ReceiptScreen /></Protected>} />
        <Route path="/services/electricity"  element={<Protected><ElectricityScreen /></Protected>} />
        <Route path="/services/water"        element={<Protected><WaterScreen /></Protected>} />
        <Route path="/services/gas"          element={<Protected><GasScreen /></Protected>} />
        <Route path="/services/municipal"    element={<Protected><MunicipalScreen /></Protected>} />
        <Route path="/services/complaints"   element={<Protected><ComplaintsScreen /></Protected>} />

        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>

      {activeInput && (
        <Keyboard onKeyPress={handleKeyPress} onClose={blurInput} />
      )}
    </>
  );
}
