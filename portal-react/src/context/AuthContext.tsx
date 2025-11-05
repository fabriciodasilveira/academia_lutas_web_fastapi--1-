// portal-react/src/context/AuthContext.tsx
import { createContext, useContext, useState, useEffect } from 'react';
import axios from 'axios';

// Este é o tipo de usuário que sua API retorna em /api/v1/portal/me
interface UserProfile {
  id: number;
  nome: string;
  email: string;
  foto: string | null;
  status_geral: string;
  // Adicione outros campos do seu schema AlunoRead
}

interface AuthContextType {
  token: string | null;
  user: UserProfile | null;
  login: (token: string) => Promise<void>;
  logout: () => void;
  isLoading: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider = ({ children }: { children: React.ReactNode }) => {
  const [token, setToken] = useState<string | null>(localStorage.getItem('react-token'));
  const [user, setUser] = useState<UserProfile | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchUser = async () => {
      if (token) {
        // Define o token nos cabeçalhos do axios
        axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
        try {
          // Busca o perfil do usuário (igual seu api.js faz)
          const response = await axios.get('/api/v1/portal/me');
          setUser(response.data);
        } catch (error) {
          console.error('Falha ao buscar usuário, limpando token.', error);
          setToken(null); // Token inválido
          localStorage.removeItem('react-token');
          delete axios.defaults.headers.common['Authorization'];
        }
      }
      setIsLoading(false);
    };
    fetchUser();
  }, [token]);

  const login = async (newToken: string) => {
    setToken(newToken);
    localStorage.setItem('react-token', newToken);
    setIsLoading(true); // Ativa o loading para buscar o novo usuário
  };

  const logout = () => {
    setToken(null);
    setUser(null);
    localStorage.removeItem('react-token');
    delete axios.defaults.headers.common['Authorization'];
  };

  return (
    <AuthContext.Provider value={{ token, user, login, logout, isLoading }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth deve ser usado dentro de um AuthProvider');
  }
  return context;
};