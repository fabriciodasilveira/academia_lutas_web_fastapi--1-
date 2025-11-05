// portal-react/src/api.ts
import axios from 'axios';
// A sintaxe "import type" é crucial
import { loadStripe } from '@stripe/stripe-js';
import type { Stripe } from '@stripe/stripe-js'; // <-- Esta linha é a chave

let stripePromise: Promise<Stripe | null>;

/**
 * Carrega a instância do Stripe de forma assíncrona.
 * Busca a chave pública da nossa API FastAPI.
 *
 */
export const getStripe = () => {
  if (!stripePromise) {
    stripePromise = (async () => {
      try {
        // O proxy do Vite (vite.config.ts) redireciona isso para localhost:8000
        const response = await axios.get('/api/v1/pagamentos/stripe-key');
        const keyData = response.data;
        
        if (keyData && keyData.publicKey) {
          return await loadStripe(keyData.publicKey);
        } else {
          throw new Error("Chave pública da Stripe não recebida.");
        }
      } catch (error) {
        console.error("Erro ao carregar o Stripe:", error);
        return null;
      }
    })();
  }
  return stripePromise;
};

/**
 * Chama o backend para criar uma sessão de checkout e redireciona o usuário.
 *
 */
export const redirectToCheckout = async (tipo: 'mensalidade' | 'inscricao', id: number) => {
  const stripe = await getStripe();
  if (!stripe) {
    throw new Error("Sistema de pagamento não inicializado.");
  }
  
  let endpoint = '';
  if (tipo === 'mensalidade') {
    endpoint = `/api/v1/pagamentos/stripe/mensalidade/${id}`;
  } else if (tipo === 'inscricao') {
    endpoint = `/api/v1/pagamentos/stripe/evento/${id}`;
  } else {
    throw new Error("Tipo de pagamento inválido.");
  }

  // 1. Chama o *nosso* backend (FastAPI) para criar a sessão
  const sessionResponse = await axios.post(endpoint);
  const sessionData = sessionResponse.data;

  if (sessionData.sessionId) {
    // 2. Redireciona o *cliente* para a página de pagamento do Stripe
    // Esta é a linha que dá o erro se os tipos estiverem errados
    const { error } = await stripe.redirectToCheckout({
      sessionId: sessionData.sessionId,
    });
    
    // Se o usuário for redirecionado, este código não roda
    // Se houver um erro antes de redirecionar (ex: sessão inválida), ele é lançado
    if (error) {
      throw new Error(error.message);
    }
  } else {
    throw new Error("Não foi possível criar a sessão de pagamento.");
  }
};