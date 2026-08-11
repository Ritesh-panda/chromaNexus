import api from './axios';
import { MOCK_USER } from '../constants/mockData';
import type { User } from '../types';

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
    // Simulated network delay
    await new Promise((resolve) => setTimeout(resolve, 800));
    // Simulated auth check
    if (params.email.includes('error')) {
      throw new Error('Invalid credentials provided.');
    }
    const token = 'mock_jwt_token_chronanexus_' + Date.now();
    localStorage.setItem('chronanexus_auth_token', token);
    return { user: { ...MOCK_USER, email: params.email }, token };
  },

  async signup(params: SignupParams): Promise<{ user: User; token: string }> {
    await new Promise((resolve) => setTimeout(resolve, 1000));
    const newUser: User = {
      ...MOCK_USER,
      name: params.name,
      email: params.email,
      role: params.role,
    };
    const token = 'mock_jwt_token_chronanexus_' + Date.now();
    localStorage.setItem('chronanexus_auth_token', token);
    return { user: newUser, token };
  },

  async logout(): Promise<void> {
    await new Promise((resolve) => setTimeout(resolve, 300));
    localStorage.removeItem('chronanexus_auth_token');
  },

  async getCurrentUser(): Promise<User> {
    await new Promise((resolve) => setTimeout(resolve, 400));
    return MOCK_USER;
  },

  async requestPasswordReset(email: string): Promise<boolean> {
    await new Promise((resolve) => setTimeout(resolve, 600));
    return true;
  },

  async verifyOTP(otp: string): Promise<boolean> {
    await new Promise((resolve) => setTimeout(resolve, 800));
    return otp.length === 6;
  },
};
