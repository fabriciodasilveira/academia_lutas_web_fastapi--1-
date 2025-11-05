// portal-react/src/pages/Carteirinha.tsx
import { useAuth } from '../context/AuthContext';
import { Spinner } from 'react-bootstrap';

// Estilos CSS embutidos (copiados do seu carteirinha.html)
//
const cardContainerStyle = { maxWidth: '450px', margin: 'auto' };
const idCardStyle = {
  backgroundColor: '#fff',
  borderRadius: '15px',
  boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
  padding: '2rem',
  border: '1px solid #e0e0e0',
};
const idCardHeaderStyle = {
  textAlign: 'center' as 'center',
  borderBottom: '2px solid #2563eb', // Cor primária
  paddingBottom: '1rem',
  marginBottom: '1.5rem',
};
const idCardPhotoStyle = {
  width: '120px',
  height: '120px',
  borderRadius: '50%',
  objectFit: 'cover' as 'cover',
  border: '4px solid #2563eb', // Cor primária
  margin: '0 auto 1rem auto',
  display: 'block',
};

const Carteirinha = () => {
  const { user, isLoading } = useAuth(); // Pega o usuário logado

  if (isLoading) {
    return <div className="text-center mt-5"><Spinner animation="border" variant="primary" /></div>;
  }
  
  if (!user) {
    return <p className="text-danger">Não foi possível carregar os dados do usuário.</p>;
  }

  // Lógica do PWA antigo
  const dataNasc = user.data_nascimento
    ? new Date(user.data_nascimento + 'T00:00:00').toLocaleDateString('pt-BR')
    : '--/--/----';
    
  const statusTexto = user.status_geral === "Ativo" ? "Aluno Ativo" : "Aluno Inativo";
  const statusClasse = user.status_geral === "Ativo" ? "bg-success" : "bg-secondary";

  return (
    <div style={cardContainerStyle}>
      <div style={idCardStyle}>
        <div style={idCardHeaderStyle}>
          {/* Você precisa copiar a imagem 'nova.png' para a pasta 'portal-react/public/images' */}
          <img src="/portal/images/nova.png" alt="Logo Academia" style={{ height: '80px', marginBottom: '0.5rem' }} />
          <h5>Carteirinha de Aluno</h5>
        </div>

        <img 
          src={user.foto || '/portal/images/default-avatar.png'} // Avatar padrão
          alt="Foto do Aluno" 
          style={idCardPhotoStyle}
        />

        <div className="id-card-body">
          <h4 className="text-center mb-4">{user.nome}</h4>
          <p><i className="fas fa-hashtag fa-fw text-primary me-2"></i> Matrícula: <strong>{1000 + user.id}</strong></p>
          <p><i className="fas fa-birthday-cake fa-fw text-primary me-2"></i> {dataNasc}</p>
          <p><i className="fas fa-phone fa-fw text-primary me-2"></i> {user.telefone || 'Não informado'}</p>
          <p><i className="fas fa-envelope fa-fw text-primary me-2"></i> {user.email || 'Não informado'}</p>
          <p className="mt-3 text-center">
            <span className={`badge fs-6 ${statusClasse}`}>{statusTexto}</span>
          </p>
        </div>
      </div>
    </div>
  );
};

export default Carteirinha;