import { api } from './axios';
import { MOCK_PATIENT, MOCK_USER } from '@/constants/mockData';
import type { Patient, User } from '@/types';

export const patientService = {
  async getProfile(): Promise<{ user: User; patient: Patient }> {
    try {
      const [userRes, patientRes] = await Promise.all([
        api.get<User>('/users/me'),
        api.get<Patient>('/patients/me'),
      ]);
      if (userRes.data && patientRes.data) {
        return { user: userRes.data, patient: patientRes.data };
      }
    } catch {
      // Fallback
    }
    await new Promise((resolve) => setTimeout(resolve, 200));
    return { user: MOCK_USER, patient: MOCK_PATIENT };
  },

  async updatePatient(data: Partial<Patient>): Promise<Patient> {
    try {
      const response = await api.put<Patient>('/patients/me', data);
      if (response.data) {
        return response.data;
      }
    } catch {
      // Fallback
    }
    return { ...MOCK_PATIENT, ...data };
  },

  async updateUser(data: Partial<User>): Promise<User> {
    try {
      const response = await api.put<User>('/users/me', data);
      if (response.data) {
        return response.data;
      }
    } catch {
      // Fallback
    }
    return { ...MOCK_USER, ...data };
  },
};
