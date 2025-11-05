// portal-react/src/components/MainLayout.tsx
import { NavLink, useNavigate, Outlet } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Navbar, Container, Button } from 'react-bootstrap';

// CSS embutido para a barra de navegação (baseado no seu style.css)
const navStyle = {
  position: 'fixed' as 'fixed',
  bottom: 0,
  width: '100%',
  height: '56px',
  boxShadow: '0 0 3px rgba(0, 0, 0, 0.2)',
  backgroundColor: '#2563eb', // Cor primária do seu PWA
  display: 'flex',
  zIndex: 1000,
};

const navLinkStyle = (isActive: boolean) => ({
  display: 'flex',
  flexDirection: 'column' as 'column',
  alignItems: 'center',
  justifyContent: 'center',
  flexGrow: 1,
  textDecoration: 'none',
  color: isActive ? '#FFFFFF' : '#cce5ff', // Cor branca para ativo, azul claro para inativo
  padding: '5px 0',
});

const navIconStyle = { fontSize: '18px' };
const navTextStyle = { fontSize: '12px' };

const MainLayout = () => {
  const { logout, user } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login', { replace: true });
  };

  return (
    <>
      <Navbar bg="primary" variant="dark" className="shadow-sm">
        <Container fluid>
          <Navbar.Brand as={NavLink} to="/dashboard">
            {/* Usando o nome do usuário ou "Portal" */}
            Olá, {user?.nome.split(' ')[0] || 'Aluno'}
          </Navbar.Brand>
          <Button variant="outline-light" onClick={handleLogout}>
            <i className="fas fa-sign-out-alt"></i> Sair
          </Button>
        </Container>
      </Navbar>

      <main className="container py-4" style={{ paddingBottom: '70px' }}>
        <Outlet /> {/* Aqui entram as páginas (Dashboard, Payments, etc) */}
      </main>

      <nav style={navStyle}>
        <NavLink to="/dashboard" style={({isActive}) => navLinkStyle(isActive)}>
          <i className="fas fa-user" style={navIconStyle}></i>
          <span style={navTextStyle}>Perfil</span>
        </NavLink>
        <NavLink to="/payments" style={({isActive}) => navLinkStyle(isActive)}>
          <i className="fas fa-file-invoice-dollar" style={navIconStyle}></i>
          <span style={navTextStyle}>Pagamentos</span>
        </NavLink>
        <NavLink to="/events" style={({isActive}) => navLinkStyle(isActive)}>
          <i className="fas fa-calendar-alt" style={navIconStyle}></i>
          <span style={navTextStyle}>Eventos</span>
        </NavLink>
        <NavLink to="/carteirinha" style={({isActive}) => navLinkStyle(isActive)}>
          <i className="fas fa-id-card" style={navIconStyle}></i>
          <span style={navTextStyle}>Carteirinha</span>
        </NavLink>
        <NavLink to="/beneficios" style={({isActive}) => navLinkStyle(isActive)}>
          <i className="fas fa-handshake" style={navIconStyle}></i>
          <span style={navTextStyle}>Benefícios</span>
        </NavLink>
      </nav>
    </>
  );
};

export default MainLayout;