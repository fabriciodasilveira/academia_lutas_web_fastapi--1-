// portal-react/src/App.tsx
import { BrowserRouter, Routes, Route, Navigate, useNavigate } from 'react-router-dom';
import { useEffect } from 'react';
import { useAuth } from './context/AuthContext';
import { Spinner } from 'react-bootstrap';

// Layouts
import MainLayout from './components/MainLayout';
import ProtectedRoute from './components/ProtectedRoute';

// Páginas
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import Payments from './pages/Payments';        // <-- NOVA
import Events from './pages/Events';          // <-- NOVA
import Carteirinha from './pages/Carteirinha';  // <-- NOVA
import Beneficios from './pages/Beneficios';    // <-- BÔNUS
import EditProfile from './pages/EditProfile';  // <-- BÔNUS

function App() {
  return (
    // basename="/portal-react" é crucial para o deploy em /portal-react
    <BrowserRouter basename="/portal-react">
      <Routes>
        {/* Rotas Públicas */}
        <Route path="/login" element={<Login />} />
        <Route path="/login/callback" element={<GoogleCallbackHandler />} />

        {/* Rotas Privadas (Exigem login) */}
        <Route element={<ProtectedRoute />}>
          <Route element={<MainLayout />}> {/* Layout com Header e Navbar */}
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/payments" element={<Payments />} />
            <Route path="/events" element={<Events />} />
            <Route path="/carteirinha" element={<Carteirinha />} />
            <Route path="/beneficios" element={<Beneficios />} />
            <Route path="/edit-profile" element={<EditProfile />} />
            
            {/* Rota padrão se logado */}
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
          </Route>
        </Route>

        {/* Rota padrão se não logado */}
        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

// Componente que cuida do redirecionamento do Google
// (Baseado em portal_aluno_pwa/js/app.js)
const GoogleCallbackHandler = () => {
  const navigate = useNavigate();
  const { login } = useAuth();
  
  // Pega o token da URL (ex: #/login/callback?token=...)
  // No React, o hash (fragmento) não é pego pelo searchParams,
  // mas como o FastAPI redireciona para /portal#/login/callback?token=...
  // o app.js antigo tratava isso.
  // A MELHOR SOLUÇÃO é o FastAPI redirecionar para:
  // /portal-react/login/callback?token=... (com ? em vez de #)
  
  // Este código assume que o FastAPI foi ajustado (como faremos no main.py)
  // para usar search params (?) e não hash (#)
  const token = new URLSearchParams(window.location.search).get('token');

  useEffect(() => {
    if (token) {
      try {
        // Valida o token (igual o PWA antigo faz)
        const payload = JSON.parse(atob(token.split('.')[1]));
        if (payload.role !== 'aluno') {
          throw new Error('Acesso negado');
        }
        
        login(token).then(() => {
          navigate('/dashboard', { replace: true });
        });
      } catch (e) {
        console.error("Token inválido ou acesso negado", e);
        navigate('/login', { replace: true });
      }
    } else {
      navigate('/login', { replace: true });
    }
  }, [token, login, navigate]);
  
  // Mostra um loading enquanto processa o token
  return (
    <div className="d-flex justify-content-center align-items-center" style={{ height: '100vh' }}>
      <Spinner animation="border" variant="primary" />
      <p className="ms-3">Autenticando...</p>
    </div>
  );
};

export default App;