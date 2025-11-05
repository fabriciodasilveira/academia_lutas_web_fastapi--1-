// portal-react/src/components/MainLayout.tsx
import { NavLink, useNavigate, Outlet } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Navbar, Container, Button } from 'react-bootstrap';

const MainLayout = () => {
  const { logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login', { replace: true });
  };

  // Recriando o seu CSS da barra de navegação inferior com React
  const navLinkStyle = ({ isActive }: { isActive: boolean }) => ({
    display: 'flex',
    flexDirection: 'column' as 'column', // TypeScript precisa disso
    alignItems: 'center',
    justifyContent: 'center',
    flexGrow: 1,
    textDecoration: 'none',
    color: isActive ? '#FFFFFF' : '#cce5ff', // Cor ativa e inativa
    padding: '5px 0'
  });

  const navIconStyle = { fontSize: '18px' };
  const navTextStyle = { fontSize: '12px' };

  return (
    <>
      {/* 1. Header (Navbar Superior) */}
      <Navbar bg="primary" variant="dark" className="shadow-sm">
        <Container fluid>
          <Navbar.Brand as={NavLink} to="/dashboard">
            {/* Você pode colocar seu logo aqui */}
            AZE Studio
          </Navbar.Brand>
          <Button variant="outline-light" onClick={handleLogout}>
            <i className="fas fa-sign-out-alt"></i> Sair
          </Button>
        </Container>
      </Navbar>

      {/* 2. O Conteúdo da Página (Dashboard, Payments, etc.) */}
      <main className="container py-4" style={{ paddingBottom: '70px' }}>
        <Outlet /> {/* O <Outlet> renderiza o componente da rota filha */}
      </main>

      {/* 3. Navbar Inferior (Fixa) */}
      <nav style={{
        position: 'fixed', bottom: 0, width: '100%', 
        height: '56px', boxShadow: '0 0 3px rgba(0, 0, 0, 0.2)',
        backgroundColor: '#2563eb', display: 'flex'
      }}>
        <NavLink to="/dashboard" style={navLinkStyle}>
          <i className="fas fa-user" style={navIconStyle}></i>
          <span style={navTextStyle}>Perfil</span>
        </NavLink>
        <NavLink to="/payments" style={navLinkStyle}>
          <i className="fas fa-file-invoice-dollar" style={navIconStyle}></i>
          <span style={navTextStyle}>Pagamentos</span>
        </NavLink>
        <NavLink to="/events" style={navLinkStyle}>
          <i className="fas fa-calendar-alt" style={navIconStyle}></i>
          <span style={navTextStyle}>Eventos</span>
        </NavLink>
        <NavLink to="/carteirinha" style={navLinkStyle}>
          <i className="fas fa-id-card" style={navIconStyle}></i>
          <span style={navTextStyle}>Carteirinha</span>
        </NavLink>
         <NavLink to="/beneficios" style={navLinkStyle}>
          <i className="fas fa-handshake" style={navIconStyle}></i>
          <span style={navTextStyle}>Benefícios</span>
        </NavLink>
      </nav>
    </>
  );
};

export default MainLayout;