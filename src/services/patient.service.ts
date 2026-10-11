import { api } from './axios';
import { MOCK_PATIENT, MOCK_USER, MOCK_DISEASES, MOCK_MEDICATIONS, MOCK_LAB_RESULTS } from '@/constants/mockData';
import type { Patient, User, Disease, Medication, LabResult } from '@/types';

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

  async getDiagnoses(): Promise<Disease[]> {
    try {
      const response = await api.get<Disease[]>('/patients/me/diagnoses');
      if (response.data && Array.isArray(response.data)) {
        return response.data;
      }
    } catch {
      // Fallback
    }
    return MOCK_DISEASES;
  },

  async getMedications(): Promise<Medication[]> {
    try {
      const response = await api.get<Medication[]>('/patients/me/medications');
      if (response.data && Array.isArray(response.data)) {
        return response.data;
      }
    } catch {
      // Fallback
    }
    return MOCK_MEDICATIONS;
  },

  async getLabResults(): Promise<LabResult[]> {
    try {
      const response = await api.get<LabResult[]>('/patients/me/labs');
      if (response.data && Array.isArray(response.data)) {
        return response.data;
      }
    } catch {
      // Fallback
    }
    return MOCK_LAB_RESULTS;
  },
};
