import api from '@/services/axios';
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
    const response = await api.post('/auth/login', {
      email: params.email,
      password: params.password,
      rememberMe: params.rememberMe ?? true,
    });
    const { user, access_token } = response.data;
    localStorage.setItem('chronanexus_auth_token', access_token);
    return { user, token: access_token };
  },

  async signup(params: SignupParams): Promise<{ user: User; token: string }> {
    const response = await api.post('/auth/signup', params);
    const { user, access_token } = response.data;
    localStorage.setItem('chronanexus_auth_token', access_token);
    return { user, token: access_token };
  },

  async logout(): Promise<void> {
    try {
      await api.post('/auth/logout');
    } catch {
      // Ignore network errors on logout
    } finally {
      localStorage.removeItem('chronanexus_auth_token');
      localStorage.removeItem('chronanexus_auth_user');
    }
  },

  async getCurrentUser(): Promise<User | null> {
    try {
      const response = await api.get('/auth/me');
      return response.data;
    } catch {
      return null;
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
