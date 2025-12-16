/* eslint-disable react-refresh/only-export-components */
import { useState, useEffect, createContext, useContext } from 'react';
import type { ReactNode } from 'react';
import { useNavigate } from 'react-router-dom';
import { authAPI } from '../lib/api';
import { analytics, Events } from '../lib/analytics';
import { getStoredUTM } from '../lib/utm';
import type { User, ExperienceLevel } from '../types';

interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (email: string, password: string, redirectTo?: string) => Promise<void>;
  register: (email: string, password: string, full_name: string, experience_level?: ExperienceLevel) => Promise<void>;
  logout: () => void;
  refreshUser: () => Promise<void>;
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
          const userData = response.data;
          setUser(userData);

          // Identify returning user for analytics
          analytics.identify(String(userData.id), {
            email: userData.email,
            tier: userData.subscription_tier || 'free',
          });
        } catch {
          // Token is invalid, clear it
          localStorage.removeItem('access_token');
          localStorage.removeItem('refresh_token');
        }
      }

      setIsLoading(false);
    };

    checkAuth();
  }, []);

  const login = async (email: string, password: string, redirectTo?: string) => {
    const response = await authAPI.login(email, password);
    const { access_token, refresh_token } = response.data;

    localStorage.setItem('access_token', access_token);
    if (refresh_token) {
      localStorage.setItem('refresh_token', refresh_token);
    }

    // Fetch user data after storing token
    const userResponse = await authAPI.getCurrentUser();
    const userData = userResponse.data;
    setUser(userData);

    // Track login event
    analytics.identify(String(userData.id), {
      email: userData.email,
      tier: userData.subscription_tier || 'free',
    });
    analytics.track(Events.USER_LOGGED_IN, {
      login_method: 'email',
      ...getStoredUTM(),
    });

    // Navigate to intended destination or default to dashboard
    navigate(redirectTo || '/dashboard');
  };

  const register = async (email: string, password: string, full_name: string, experience_level?: ExperienceLevel) => {
    // Register creates the user but doesn't return a token
    await authAPI.register(email, password, full_name, experience_level);

    // Login to get the token
    const loginResponse = await authAPI.login(email, password);
    const { access_token, refresh_token } = loginResponse.data;

    localStorage.setItem('access_token', access_token);
    if (refresh_token) {
      localStorage.setItem('refresh_token', refresh_token);
    }

    // Fetch user data
    const userResponse = await authAPI.getCurrentUser();
    const userData = userResponse.data;
    setUser(userData);

    // Track registration event
    analytics.identify(String(userData.id), {
      email: userData.email,
      tier: 'free', // New users start on free tier
    });
    analytics.track(Events.USER_REGISTERED, {
      signup_method: 'email',
      experience_level: experience_level || 'unknown',
      ...getStoredUTM(),
    });

    navigate('/dashboard');
  };

  const logout = () => {
    // Track logout before resetting analytics
    analytics.track(Events.USER_LOGGED_OUT);
    analytics.reset();

    authAPI.logout();
    setUser(null);
    navigate('/login');
  };

  const refreshUser = async () => {
    try {
      const response = await authAPI.getCurrentUser();
      setUser(response.data);
    } catch (error) {
      // If refresh fails, user might need to re-login
      console.error('Failed to refresh user:', error);
    }
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
        refreshUser,
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
