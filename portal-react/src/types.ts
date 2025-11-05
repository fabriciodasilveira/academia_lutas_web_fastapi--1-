// portal-react/src/types.ts

// Formato do seu Schema AlunoRead (de src/schemas/aluno.py)
//
export interface UserProfile {
  id: number;
  nome: string;
  email: string;
  foto: string | null;
  status_geral: string;
  data_nascimento: string | null;
  cpf: string | null;
  telefone: string | null;
  endereco: string | null;
  observacoes: string | null;
  nome_responsavel: string | null;
  cpf_responsavel: string | null;
  parentesco_responsavel: string | null;
  telefone_responsavel: string | null;
  email_responsavel: string | null;
}

// Formato do seu Schema PendenciaFinanceira (de src/schemas/portal_aluno.py)
//
export interface PendenciaFinanceira {
  tipo: 'mensalidade' | 'inscricao';
  id: number;
  descricao: string;
  data_vencimento: string; // A API envia como string "YYYY-MM-DD"
  valor: number;
  status: 'pendente' | 'pago' | 'cancelado';
}

// Formato do seu Schema EventoRead (de src/schemas/evento.py)
//
export interface Evento {
  id: number;
  nome: string;
  tipo: string | null;
  descricao: string | null;
  local: string | null;
  data_evento: string; // A API envia como string (ISODateTime)
  valor_inscricao: number;
  status: string;
  is_inscrito: boolean; // Campo customizado da sua API
}