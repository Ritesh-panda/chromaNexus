import React, { createContext, useContext, useState, useEffect } from 'react';
import type { User } from '@/types';
import { MOCK_USER } from '@/constants/mockData';
import { authService } from '@/services/auth.service';
import type { LoginParams, SignupParams } from '@/services/auth.service';


interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (params: LoginParams) => Promise<void>;
  signup: (params: SignupParams) => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(MOCK_USER); // Logged in by default for interactive demo experience
  const [isLoading, setIsLoading] = useState<boolean>(false);

  useEffect(() => {
    const token = localStorage.getItem('chronanexus_auth_token');
    if (token) {
      setUser(MOCK_USER);
    }
  }, []);

  const login = async (params: LoginParams) => {
    setIsLoading(true);
    try {
      const res = await authService.login(params);
      setUser(res.user);
    } finally {
      setIsLoading(false);
    }
  };

  const signup = async (params: SignupParams) => {
    setIsLoading(true);
    try {
      const res = await authService.signup(params);
      setUser(res.user);
    } finally {
      setIsLoading(false);
    }
  };

  const logout = async () => {
    setIsLoading(true);
    try {
      await authService.logout();
      setUser(null);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <AuthContext.Provider value={{ user, isAuthenticated: !!user, isLoading, login, signup, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
