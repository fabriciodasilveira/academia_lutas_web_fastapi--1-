// portal-react/src/pages/Dashboard.tsx
import { useAuth } from '../context/AuthContext';

const Dashboard = () => {
  const { user } = useAuth(); // Pega o usuário do nosso Contexto

  if (!user) {
    return <div>Carregando perfil...</div>;
  }

  // Converte a data (exemplo)
  const dataNasc = user.data_nascimento 
    ? new Date(user.data_nascimento + 'T00:00:00').toLocaleDateString('pt-BR') 
    : 'Não informada';

  return (
    <div>
      <h3>Meu Perfil</h3>
      <div className="card mb-4">
        <div className="card-body">
          {/* O HTML é o mesmo do seu dashboard.html, mas como JSX */}
          <div className="d-flex align-items-center">
            <img 
              id="profile-picture" 
              src={user.foto || '/portal/images/default-avatar.png'} 
              alt="Foto do Perfil" 
              className="rounded-circle me-3" 
              style={{ width: '80px', height: '80px', objectFit: 'cover' }}
            />
            <div>
              <h5 className="card-title mb-0">{user.nome}</h5>
              <p className="card-text text-muted">{user.email}</p>
            </div>
          </div>
          <hr />
          <p className="card-text"><strong>Telefone:</strong> {user.telefone || 'Não informado'}</p>
          <p className="card-text"><strong>Data de Nascimento:</strong> {dataNasc}</p>
          {/* Você pode buscar as matrículas aqui com um useEffect e axios */}
        </div>
      </div>
    </div>
  );
};

export default Dashboard;