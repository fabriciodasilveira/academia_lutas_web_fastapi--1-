// portal-react/src/components/ProtectedRoute.tsx
import { Navigate, Outlet } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Spinner } from 'react-bootstrap';

const ProtectedRoute = () => {
  const { token, isLoading } = useAuth();

  if (isLoading) {
    // Se estiver carregando, mostre um spinner
    return (
      <div className="d-flex justify-content-center align-items-center" style={{ height: '100vh' }}>
        <Spinner animation="border" variant="primary" />
      </div>
    );
  }

  // Se terminou de carregar e NÃO tem token, mande para /login
  if (!token) {
    return <Navigate to="/login" replace />;
  }

  // Se terminou e TEM token, mostre o layout com a página
  return <Outlet />; // <Outlet> aqui será o <MainLayout> que definimos no App.tsx
};

export default ProtectedRoute;