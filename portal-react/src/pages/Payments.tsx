// portal-react/src/pages/Payments.tsx
import { useEffect, useState } from 'react';
import axios from 'axios';
import { PendenciaFinanceira } from '../types';
import { ListGroup, Spinner, Alert, Button } from 'react-bootstrap';
import { redirectToCheckout } from '../api'; // Importa nossa função do Stripe

const Payments = () => {
  const [pendencias, setPendencias] = useState<PendenciaFinanceira[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const [pagandoId, setPagandoId] = useState<string | null>(null); // ID único (ex: "mensalidade-1")

  useEffect(() => {
    // Busca as pendências (mensalidades e eventos)
    const fetchPendencias = async () => {
      try {
        setError('');
        setIsLoading(true);
        // Endpoint do portal_aluno_fastapi.py
        const response = await axios.get('/api/v1/portal/pendencias');
        
        // Ordena pendentes primeiro, depois por data
        const sorted = response.data.sort((a: PendenciaFinanceira, b: PendenciaFinanceira) => 
          (a.status === 'pendente' ? -1 : 1) - (b.status === 'pendente' ? -1 : 1) || 
          new Date(b.data_vencimento).getTime() - new Date(a.data_vencimento).getTime()
        );
        setPendencias(sorted);
      } catch (err) {
        setError('Não foi possível carregar suas pendências.');
      }
      setIsLoading(false);
    };
    fetchPendencias();
  }, []);

  const handlePay = async (tipo: 'mensalidade' | 'inscricao', id: number) => {
    const uniqueId = `${tipo}-${id}`;
    setPagandoId(uniqueId); // Ativa o spinner do botão
    setError('');
    try {
      // Chama a função da api.ts
      await redirectToCheckout(tipo, id);
      // O usuário será redirecionado para o Stripe.
    } catch (err: any) {
      setError(err.message || 'Não foi possível iniciar o pagamento.');
      setPagandoId(null); // Para o spinner em caso de erro
    }
  };

  if (isLoading) {
    return <div className="text-center mt-5"><Spinner animation="border" variant="primary" /></div>;
  }

  return (
    <div>
      <h3 className="mb-4">Minhas Mensalidades</h3>
      {error && <Alert variant="danger">{error}</Alert>}
      
      <ListGroup id="payments-list">
        {pendencias.length === 0 ? (
          <p className="text-muted text-center mt-4">Nenhuma pendência financeira encontrada.</p>
        ) : (
          pendencias.map(p => {
            const uniqueId = `${p.tipo}-${p.id}`;
            return (
              <ListGroup.Item key={uniqueId} className="d-flex flex-wrap justify-content-between align-items-center">
                <div className="me-auto">
                  <h6 className="mb-1">
                    <i className={`fas ${p.tipo === 'mensalidade' ? 'fa-file-invoice-dollar' : 'fa-calendar-alt'} me-2 text-muted`}></i>
                    {p.descricao}
                  </h6>
                  <small className="text-muted">
                    Vencimento: {new Date(p.data_vencimento + 'T00:00:00').toLocaleDateString('pt-BR')} | Valor: R$ {p.valor.toFixed(2).replace('.', ',')}
                  </small>
                </div>
                <div className="mt-2 mt-md-0">
                  {p.status === 'pendente' && p.valor > 0 ? (
                    <Button 
                      size="sm" 
                      variant="primary" 
                      onClick={() => handlePay(p.tipo, p.id)}
                      disabled={pagandoId === uniqueId}
                    >
                      {pagandoId === uniqueId ? (
                        <Spinner as="span" size="sm" animation="border" />
                      ) : (
                        <><i className="fas fa-credit-card me-1"></i> Pagar Online</>
                      )}
                    </Button>
                  ) : (
                    <span className={`badge bg-${p.status === 'pago' ? 'success' : 'secondary'}`}>
                      {p.status.charAt(0).toUpperCase() + p.status.slice(1)}
                    </span>
                  )}
                </div>
              </ListGroup.Item>
            )
          })
        )}
      </ListGroup>
    </div>
  );
};

export default Payments;