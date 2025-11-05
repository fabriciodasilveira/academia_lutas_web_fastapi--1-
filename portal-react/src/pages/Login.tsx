// portal-react/src/pages/Login.tsx
import { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import axios from 'axios';
import { Container, Row, Col, Card, Form, Button, Alert } from 'react-bootstrap';
import { useNavigate } from 'react-router-dom';

const Login = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    // A API de token espera dados de formulário
    const formData = new URLSearchParams();
    formData.append('username', email);
    formData.append('password', password);

    try {
      // Usamos o axios.post. O proxy do Vite vai redirecionar para localhost:8000
      const response = await axios.post('/api/v1/auth/token', formData, {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
      });

      const { access_token, user_info } = response.data;

      // Verifica se é aluno (igual seu PWA faz)
      if (user_info.role !== 'aluno') {
        throw new Error('Acesso permitido somente a alunos.');
      }

      await login(access_token); // Salva o token no Context
      navigate('/dashboard'); // Redireciona

    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Email ou senha inválidos.');
    }
  };

  // URL para o login do Google (a API cuidará do redirecionamento)
  const googleLoginUrl = '/api/v1/auth/login/google?origin=pwa';

  return (
    <Container>
      <Row className="justify-content-center align-items-center" style={{ minHeight: '80vh' }}>
        <Col md={10} lg={8}>
          {error && <Alert variant="danger">{error}</Alert>}
          <Card className="shadow-sm">
            <Card.Body className="p-4">
              <h3 className="text-center">Portal do Aluno</h3>
              <Form onSubmit={handleSubmit}>
                <Form.Group className="mb-3">
                  <Form.Label>Email</Form.Label>
                  <Form.Control type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
                </Form.Group>
                <Form.Group className="mb-3">
                  <Form.Label>Senha</Form.Label>
                  <Form.Control type="password" value={password} onChange={(e) => setPassword(e.target.value)} required />
                </Form.Group>
                <div className="d-grid mt-4">
                  <Button type="submit" variant="primary">Entrar</Button>
                </div>
              </Form>
              {/* ... Botão do Google ... */}
              <div className="text-center my-3"><hr /><span>OU</span></div>
              <div className="d-grid">
                  <Button href={googleLoginUrl} variant="outline-secondary">
                      Entrar com Google
                  </Button>
              </div>
            </Card.Body>
          </Card>
        </Col>
      </Row>
    </Container>
  );
};

export default Login;