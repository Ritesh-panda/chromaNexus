import api from '@/services/axios';
import { MOCK_USER } from '@/constants/mockData';
import type { User } from '@/types';

export interface LoginParams {
  email: string;
  password: string;
  rememberMe?: boolean;
}

export interface SignupParams {
  name: string;
  email: string;
  password: string;
  role: 'patient' | 'doctor';
}

export const authService = {
  async login(params: LoginParams): Promise<{ user: User; token: string }> {
    try {
      const response = await api.post('/auth/login', {
        email: params.email,
        password: params.password,
        rememberMe: params.rememberMe ?? true,
      });
      const { user, access_token } = response.data;
      localStorage.setItem('chronanexus_auth_token', access_token);
      return { user, token: access_token };
    } catch {
      // Fallback to local simulated auth for offline/demo development
      if (params.email.includes('error')) {
        throw new Error('Invalid credentials provided.');
      }
      const token = 'mock_jwt_token_chronanexus_' + Date.now();
      localStorage.setItem('chronanexus_auth_token', token);
      return { user: { ...MOCK_USER, email: params.email }, token };
    }
  },

  async signup(params: SignupParams): Promise<{ user: User; token: string }> {
    try {
      const response = await api.post('/auth/signup', params);
      const { user, access_token } = response.data;
      localStorage.setItem('chronanexus_auth_token', access_token);
      return { user, token: access_token };
    } catch {
      const newUser: User = {
        ...MOCK_USER,
        name: params.name,
        email: params.email,
        role: params.role,
      };
      const token = 'mock_jwt_token_chronanexus_' + Date.now();
      localStorage.setItem('chronanexus_auth_token', token);
      return { user: newUser, token };
    }
  },

  async logout(): Promise<void> {
    try {
      await api.post('/auth/logout');
    } catch {
      // Ignore network errors on logout
    } finally {
      localStorage.removeItem('chronanexus_auth_token');
    }
  },

  async getCurrentUser(): Promise<User> {
    try {
      const response = await api.get('/auth/me');
      return response.data;
    } catch {
      return MOCK_USER;
    }
  },

  async requestPasswordReset(_email: string): Promise<boolean> {
    await new Promise((resolve) => setTimeout(resolve, 600));
    return true;
  },

  async verifyOTP(otp: string): Promise<boolean> {
    await new Promise((resolve) => setTimeout(resolve, 800));
    return otp.length === 6;
  },
};
