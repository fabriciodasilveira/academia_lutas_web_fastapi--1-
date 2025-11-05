// portal-react/src/App.tsx
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import ProtectedRoute from './components/ProtectedRoute';

// Nossas páginas
import Dashboard from './pages/Dashboard';
import Payments from './pages/Payments';
import Login from './pages/Login';
// import Events from './pages/Events';
// import Carteirinha from './pages/Carteirinha';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Rotas Públicas */}
        <Route path="/login" element={<Login />} />

        {/* Rotas Privadas (usando o layout) */}
        <Route element={<ProtectedRoute />}>
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/payments" element={<Payments />} />
          {/* <Route path="/events" element={<Events />} /> */}
          {/* <Route path="/carteirinha" element={<Carteirinha />} /> */}
        </Route>

        {/* Redirecionamento padrão */}
        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;