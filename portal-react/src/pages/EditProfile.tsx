// portal-react/src/pages/EditProfile.tsx
import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { Form, Button, Card, Spinner, Alert, Row, Col } from 'react-bootstrap';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';

const EditProfile = () => {
  const { user, refetchUser, isLoading: isAuthLoading } = useAuth();
  const navigate = useNavigate();
  
  // Estado do formulário
  const [formData, setFormData] = useState({
    nome: '',
    cpf: '',
    telefone: '',
    data_nascimento: '',
    endereco: '',
    observacoes: '',
    nome_responsavel: '',
    cpf_responsavel: '',
    parentesco_responsavel: '',
    telefone_responsavel: '',
    email_responsavel: '',
  });
  const [fotoFile, setFotoFile] = useState<File | null>(null);
  const [fotoPreview, setFotoPreview] = useState<string | null>(null);
  const [showResponsavel, setShowResponsavel] = useState(false);
  
  // Estado de controle
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState('');

  // Carrega os dados do usuário no formulário
  useEffect(() => {
    if (user) {
      setFormData({
        nome: user.nome || '',
        cpf: user.cpf || '',
        telefone: user.telefone || '',
        data_nascimento: user.data_nascimento || '',
        endereco: user.endereco || '',
        observacoes: user.observacoes || '',
        nome_responsavel: user.nome_responsavel || '',
        cpf_responsavel: user.cpf_responsavel || '',
        parentesco_responsavel: user.parentesco_responsavel || '',
        telefone_responsavel: user.telefone_responsavel || '',
        email_responsavel: user.email_responsavel || '',
      });
      setFotoPreview(user.foto);
      checkIdade(user.data_nascimento);
    }
  }, [user]);

  // Função para checar idade (lógica do PWA)
  const checkIdade = (dataNasc: string | null) => {
    if (!dataNasc) {
      setShowResponsavel(false);
      return;
    }
    const hoje = new Date();
    const nascimento = new Date(dataNasc);
    let idade = hoje.getFullYear() - nascimento.getFullYear();
    const m = hoje.getMonth() - nascimento.getMonth();
    if (m < 0 || (m === 0 && hoje.getDate() < nascimento.getDate())) {
      idade--;
    }
    setShowResponsavel(idade < 18);
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
    
    if (name === 'data_nascimento') {
      checkIdade(value);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      setFotoFile(file);
      setFotoPreview(URL.createObjectURL(file)); // Mostra o preview
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSaving(true);
    setError('');

    // A API espera FormData (baseado em portal_aluno_fastapi.py)
    const data = new FormData();
    
    // Adiciona todos os campos do estado ao FormData
    // TypeScript nos força a ser explícitos
    data.append('nome', formData.nome);
    data.append('cpf', formData.cpf);
    data.append('telefone', formData.telefone);
    data.append('data_nascimento', formData.data_nascimento);
    data.append('endereco', formData.endereco);
    data.append('observacoes', formData.observacoes);
    data.append('nome_responsavel', formData.nome_responsavel);
    data.append('cpf_responsavel', formData.cpf_responsavel);
    data.append('parentesco_responsavel', formData.parentesco_responsavel);
    data.append('telefone_responsavel', formData.telefone_responsavel);
    data.append('email_responsavel', formData.email_responsavel);
    
    if (fotoFile) {
      data.append('foto', fotoFile);
    }

    try {
      // Chama o endpoint PUT
      await axios.put('/api/v1/portal/me', data, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      
      // Recarrega os dados do usuário no AuthContext
      await refetchUser(); 
      
      alert('Perfil atualizado com sucesso!');
      navigate('/dashboard');
      
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Não foi possível salvar as alterações.');
    } finally {
      setIsSaving(false);
    }
  };

  if (isAuthLoading) {
    return <div className="text-center mt-5"><Spinner animation="border" variant="primary" /></div>;
  }

  return (
    <Row className="justify-content-center">
      <Col lg={10}>
        {error && <Alert variant="danger">{error}</Alert>}
        <div className="d-flex justify-content-between align-items-center mb-4">
          <h3 className="mb-0">Editar Perfil</h3>
          <Button variant="outline-secondary" size="sm" onClick={() => navigate(-1)}>
            <i className="fas fa-arrow-left"></i> Voltar
          </Button>
        </div>

        <Card className="shadow-sm">
          <Card.Body className="p-4">
            <Form onSubmit={handleSubmit}>
              <div className="text-center mb-4">
                <img 
                  src={fotoPreview || '/portal/images/default-avatar.png'} 
                  alt="Foto do Perfil" 
                  className="rounded-circle" 
                  style={{ width: '120px', height: '120px', objectFit: 'cover' }}
                />
              </div>

              <Row className="g-3">
                <Col xs={12}>
                  <Form.Group>
                    <Form.Label>Nome Completo *</Form.Label>
                    <Form.Control type="text" name="nome" value={formData.nome} onChange={handleChange} required disabled={isSaving} />
                  </Form.Group>
                </Col>
                <Col xs={12}>
                  <Form.Group>
                    <Form.Label>Email</Form.Label>
                    <Form.Control type="email" value={user?.email || ''} readOnly disabled />
                    <Form.Text>O email é seu login e não pode ser alterado.</Form.Text>
                  </Form.Group>
                </Col>
                <Col md={6}>
                  <Form.Group>
                    <Form.Label>CPF</Form.Label>
                    <Form.Control type="text" name="cpf" value={formData.cpf} onChange={handleChange} placeholder="000.000.000-00" disabled={isSaving} />
                  </Form.Group>
                </Col>
                <Col md={6}>
                  <Form.Group>
                    <Form.Label>Telefone</Form.Label>
                    <Form.Control type="tel" name="telefone" value={formData.telefone} onChange={handleChange} placeholder="(00) 00000-0000" disabled={isSaving} />
                  </Form.Group>
                </Col>
                <Col md={6}>
                  <Form.Group>
                    <Form.Label>Data de Nascimento</Form.Label>
                    <Form.Control type="date" name="data_nascimento" value={formData.data_nascimento} onChange={handleChange} disabled={isSaving} />
                  </Form.Group>
                </Col>
                <Col md={6}>
                  <Form.Group>
                    <Form.Label>Alterar Foto</Form.Label>
                    <Form.Control type="file" accept="image/*" onChange={handleFileChange} disabled={isSaving} />
                  </Form.Group>
                </Col>
              </Row>

              {/* Seção do Responsável (condicional) */}
              {showResponsavel && (
                <Row className="g-3 border-top pt-3 mt-3">
                  <h5 className="col-12 text-primary"><i className="fas fa-user-shield me-2"></i>Dados do Responsável</h5>
                  <Col md={6}>
                    <Form.Group>
                      <Form.Label>Nome do Responsável *</Form.Label>
                      <Form.Control type="text" name="nome_responsavel" value={formData.nome_responsavel} onChange={handleChange} required disabled={isSaving} />
                    </Form.Group>
                  </Col>
                  <Col md={6}>
                    <Form.Group>
                      <Form.Label>CPF do Responsável *</Form.Label>
                      <Form.Control type="text" name="cpf_responsavel" value={formData.cpf_responsavel} onChange={handleChange} placeholder="000.000.000-00" required disabled={isSaving} />
                    </Form.Group>
                  </Col>
                  {/* ... outros campos do responsável ... */}
                </Row>
              )}
              
              <div className="d-grid mt-4">
                <Button type="submit" variant="primary" disabled={isSaving}>
                  {isSaving ? <Spinner as="span" size="sm" animation="border" /> : <><i className="fas fa-save me-1"></i> Salvar Alterações</>}
                </Button>
              </div>
            </Form>
          </Card.Body>
        </Card>
      </Col>
    </Row>
  );
};

export default EditProfile;