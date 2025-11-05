// portal-react/src/pages/Events.tsx
import { useEffect, useState } from 'react';
import axios from 'axios';
import { Evento } from '../types';
import { Card, Spinner, Alert, Button } from 'react-bootstrap';

const Events = () => {
  const [eventos, setEventos] = useState<Evento[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const [inscricaoLoading, setInscricaoLoading] = useState<number | null>(null);

  useEffect(() => {
    const fetchEventos = async () => {
      try {
        setError('');
        setIsLoading(true);
        // Endpoint do portal_aluno_fastapi.py
        const response = await axios.get('/api/v1/portal/eventos');
        setEventos(response.data);
      } catch (err) {
        setError('Não foi possível carregar os eventos.');
      }
      setIsLoading(false);
    };
    fetchEventos();
  }, []);

  const handleInscricao = async (eventoId: number) => {
    setInscricaoLoading(eventoId);
    setError('');
    try {
      // Endpoint de inscrição
      await axios.post(`/api/v1/portal/eventos/${eventoId}/inscrever`);
      
      // Atualiza o estado local do evento para "Inscrito"
      setEventos(eventos.map(e => 
        e.id === eventoId ? { ...e, is_inscrito: true } : e
      ));
      
      alert('Inscrição realizada! A pendência está na sua aba de Pagamentos.');
    } catch (err: any)
       {
      const errorMsg = err.response?.data?.detail || 'Não foi possível realizar a inscrição.';
      setError(errorMsg);
      alert(errorMsg); // Alerta o erro específico (ex: "Evento lotado")
    }
    setInscricaoLoading(null);
  };

  if (isLoading) {
    return <div className="text-center mt-5"><Spinner animation="border" variant="primary" /></div>;
  }

  return (
    <div>
      <h3 className="mb-4">Próximos Eventos</h3>
      {error && <Alert variant="danger">{error}</Alert>}
      
      <div id="events-list">
        {eventos.length === 0 ? (
          <p className="text-muted text-center mt-4">Nenhum evento futuro encontrado.</p>
        ) : (
          eventos.map(e => {
            const dataEvento = new Date(e.data_evento).toLocaleString('pt-BR', 
              { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' }
            );
            return (
              <Card key={e.id} className="mb-3 shadow-sm">
                <Card.Body>
                  <div className="d-flex justify-content-between align-items-start">
                    <div>
                      <h5 className="card-title">{e.nome}</h5>
                      <p className="card-text mb-0">
                        <small className="text-muted">{dataEvento}</small>
                      </p>
                      <p className="card-text">
                        <small className="text-muted">Valor: R$ {e.valor_inscricao.toFixed(2).replace('.', ',')}</small>
                      </p>
                    </div>
                    {e.is_inscrito ? (
                      <Button variant="success" size="sm" disabled>
                        <i className="fas fa-check me-1"></i>Inscrito
                      </Button>
                    // Lógica do PWA antigo
                    ) : e.status !== 'Planejado' ? ( 
                      <Button variant="secondary" size="sm" disabled>{e.status}</Button>
                    ) : (
                      <Button 
                        variant="primary" 
                        size="sm" 
                        onClick={() => handleInscricao(e.id)}
                        disabled={inscricaoLoading === e.id}
                      >
                        {inscricaoLoading === e.id ? (
                          <Spinner as="span" size="sm" animation="border" />
                        ) : (
                          'Inscrever-se'
                        )}
                      </Button>
                    )}
                  </div>
                  {e.descricao && <p className="card-text mt-2">{e.descricao}</p>}
                </Card.Body>
              </Card>
            );
          })
        )}
      </div>
    </div>
  );
};

export default Events;