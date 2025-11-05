// portal-react/src/context/AuthContext.tsx
import { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import axios from 'axios';
import { UserProfile } from '../types'; // <-- Importa nosso tipo

// Define o que o nosso Contexto vai fornecer
interface AuthContextType {
  token: string | null;
  user: UserProfile | null;
  login: (token: string) => Promise<void>;
  logout: () => void;
  isLoading: boolean;
  refetchUser: () => Promise<void>; // <-- Função para recarregar o usuário (ex: após editar perfil)
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

// Função que busca o usuário na API
const fetchUser = async (token: string): Promise<UserProfile> => {
  // Define o token no cabeçalho
  axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
  // Chama o endpoint /api/v1/portal/me
  const response = await axios.get('/api/v1/portal/me');
  return response.data;
};

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [token, setToken] = useState<string | null>(localStorage.getItem('react-token'));
  const [user, setUser] = useState<UserProfile | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const loadUser = async () => {
      if (token) {
        try {
          const userData = await fetchUser(token);
          setUser(userData);
        } catch (error) {
          console.error('Token inválido ou sessão expirada.', error);
          localStorage.removeItem('react-token');
          setToken(null);
          delete axios.defaults.headers.common['Authorization'];
        }
      }
      setIsLoading(false);
    };
    loadUser();
  }, [token]);

  const login = async (newToken: string) => {
    localStorage.setItem('react-token', newToken);
    setToken(newToken);
    // Não precisa de setIsLoading(true) aqui, o useEffect vai cuidar disso
  };

  const logout = () => {
    localStorage.removeItem('react-token');
    setToken(null);
    setUser(null);
    delete axios.defaults.headers.common['Authorization'];
  };

  const refetchUser = async () => {
    if (token) {
      try {
        setIsLoading(true);
        const userData = await fetchUser(token);
        setUser(userData);
        setIsLoading(false);
      } catch (error) {
        console.error('Falha ao recarregar usuário', error);
        logout(); // Desloga se não conseguir recarregar
      }
    }
  };

  return (
    <AuthContext.Provider value={{ token, user, login, logout, isLoading, refetchUser }}>
      {children}
    </AuthContext.Provider>
  );
};

// Hook customizado
export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth deve ser usado dentro de um AuthProvider');
  }
  return context;
};