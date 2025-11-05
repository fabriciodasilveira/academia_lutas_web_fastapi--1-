// portal-react/src/pages/Beneficios.tsx
import { Row, Col, Card, Button } from 'react-bootstrap';

// Lista de parceiros (hardcoded, igual ao PWA antigo)
// (Baseado em portal_aluno_pwa/js/app.js)
const partners = [
     {
        logo: '/portal/images/iron.png',
        nome: 'Centro de Treinamento Iron Gym',
        desconto: '20% de desconto na Mensalidade.',
        whatsapp: '5532985062330'
    },
    {
        logo: '/portal/images/bull.png',
        nome: 'Arthur Carvalho Duarte - ARQUITETURA E URBANISMO',
        desconto: 'Desconto de 20% em seu projeto.',
        whatsapp: '5532988810989'
    },
    {
        logo: '/portal/images/alexandria.png',
        nome: 'Alexandria Hamburgueria',
        desconto: '20% de desconto em todos os Rodízios.',
        whatsapp: '5532933003620'
    },
    {
        logo: '/portal/images/lucasStarck.png',
        nome: 'Lucas Starck - Nutricionista Esportivo',
        desconto: 'Consulta com 50% de desconto para alunos ativos.',
        whatsapp: '5532998180941'
    },
];

const Beneficios = () => {
  return (
    <div>
      <h3 className="mb-4"><i className="fas fa-handshake me-2"></i>Benefícios e Parceiros</h3>
      <p className="text-muted mb-4">Confira os descontos exclusivos para alunos da academia:</p>
      
      <Row id="partners-list">
        {partners.length === 0 ? (
           <p className="text-muted text-center mt-4">Nenhum parceiro cadastrado no momento.</p>
        ) : (
          partners.map((p, index) => {
            const mensagemWhatsapp = encodeURIComponent("Sou da Academia AZE Studio e vim pelo clube de descontos para parceiros.");
            const whatsappLink = p.whatsapp ? `https://wa.me/${p.whatsapp}?text=${mensagemWhatsapp}` : null;
            
            return (
              <Col md={6} lg={4} key={index} className="mb-4">
                <Card className="h-100 text-center shadow-sm">
                  <Card.Img 
                    variant="top" 
                    src={p.logo} 
                    alt={`Logo ${p.nome}`} 
                    style={{ maxHeight: '80px', width: 'auto', maxWidth: '150px', objectFit: 'contain', margin: '1.5rem auto 0 auto' }} 
                  />
                  <Card.Body className="d-flex flex-column">
                    <Card.Title>{p.nome}</Card.Title>
                    <Card.Text>{p.desconto}</Card.Text>
                    {whatsappLink && (
                      <Button href={whatsappLink} target="_blank" variant="success" className="mt-auto">
                        <i className="fab fa-whatsapp me-1"></i> Ir para o Parceiro
                      </Button>
                    )}
                  </Card.Body>
                </Card>
              </Col>
            );
          })
        )}
      </Row>
    </div>
  );
};

export default Beneficios;