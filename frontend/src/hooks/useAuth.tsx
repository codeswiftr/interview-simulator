import { useState, useEffect, createContext, useContext } from 'react';
import type { ReactNode } from 'react';
import { useNavigate } from 'react-router-dom';
import { authAPI } from '../lib/api';
import type { User, AuthResponse } from '../types';

interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, full_name: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const navigate = useNavigate();

  // Check for existing token on mount
  useEffect(() => {
    const checkAuth = async () => {
      const token = localStorage.getItem('access_token');

      if (token) {
        try {
          const response = await authAPI.getCurrentUser();
          setUser(response.data);
        } catch (error) {
          // Token is invalid, clear it
          localStorage.removeItem('access_token');
          localStorage.removeItem('refresh_token');
        }
      }

      setIsLoading(false);
    };

    checkAuth();
  }, []);

  const login = async (email: string, password: string) => {
    try {
      const response = await authAPI.login(email, password);
      const data: AuthResponse = response.data;

      localStorage.setItem('access_token', data.access_token);
      setUser(data.user);

      navigate('/dashboard');
    } catch (error) {
      throw error;
    }
  };

  const register = async (email: string, password: string, full_name: string) => {
    try {
      const response = await authAPI.register(email, password, full_name);
      const data: AuthResponse = response.data;

      localStorage.setItem('access_token', data.access_token);
      setUser(data.user);

      navigate('/dashboard');
    } catch (error) {
      throw error;
    }
  };

  const logout = () => {
    authAPI.logout();
    setUser(null);
    navigate('/login');
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isLoading,
        isAuthenticated: !!user,
        login,
        register,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);

  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }

  return context;
}
