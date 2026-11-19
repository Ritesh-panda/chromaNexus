import { api } from './axios';
import { MOCK_PATIENT, MOCK_USER, MOCK_DISEASES, MOCK_MEDICATIONS, MOCK_LAB_RESULTS } from '@/constants/mockData';
import type { Patient, User, Disease, Medication, LabResult, AnalyteSummary, StructuredTrendData } from '@/types';

function isDemoUser(): boolean {
  try {
    const saved = localStorage.getItem('chronanexus_auth_user');
    if (saved) {
      const u = JSON.parse(saved);
      return u?.email === 'alex.vance@example.com';
    }
  } catch {
    // Ignore
  }
  return false;
}

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
      // Fallback only if demo
    }
    if (isDemoUser()) {
      return { user: MOCK_USER, patient: MOCK_PATIENT };
    }
    throw new Error('Failed to load patient profile.');
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
    return data as Patient;
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
    return data as User;
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
    return isDemoUser() ? MOCK_DISEASES : [];
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
    return isDemoUser() ? MOCK_MEDICATIONS : [];
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
    return isDemoUser() ? MOCK_LAB_RESULTS : [];
  },

  async getAnalytes(): Promise<AnalyteSummary[]> {
    try {
      const response = await api.get<{ analytes: AnalyteSummary[] }>('/patients/me/labs/analytes');
      if (response.data?.analytes && Array.isArray(response.data.analytes)) {
        return response.data.analytes;
      }
    } catch (err) {
      console.warn('Failed to fetch analytes from API:', err);
    }
    if (!isDemoUser()) {
      return [];
    }
    // Fallback: extract distinct analytes from MOCK_LAB_RESULTS for demo only
    const map = new Map<string, AnalyteSummary>();
    MOCK_LAB_RESULTS.forEach((l) => {
      const key = l.testName.toLowerCase().trim();
      if (!map.has(key)) {
        map.set(key, {
          testName: l.testName,
          canonicalName: l.testName,
          count: 1,
          latestDate: l.testDate,
          latestValue: String(l.value),
          unit: l.unit,
          referenceRange: l.referenceRange,
          facilities: l.hospitalName ? [l.hospitalName] : ['Metro General Hospital'],
        });
      } else {
        const item = map.get(key)!;
        item.count += 1;
        if (l.testDate > (item.latestDate || '')) {
          item.latestDate = l.testDate;
          item.latestValue = String(l.value);
        }
        if (l.hospitalName && !item.facilities.includes(l.hospitalName)) {
          item.facilities.push(l.hospitalName);
        }
      }
    });
    return Array.from(map.values()).sort((a, b) => b.count - a.count);
  },

  async getLabTrend(
    analyte: string,
    timeWindow?: string,
    startDate?: string,
    endDate?: string
  ): Promise<StructuredTrendData | null> {
    try {
      const params: Record<string, string> = { analyte };
      if (timeWindow && timeWindow !== 'all') {
        params.time_window = timeWindow;
      }
      if (startDate) {
        params.start_date = startDate;
      }
      if (endDate) {
        params.end_date = endDate;
      }
      const response = await api.get<StructuredTrendData>('/patients/me/labs/trends', { params });
      if (response.data) {
        return response.data;
      }
    } catch (err) {
      console.warn('Failed to fetch lab trend from API:', err);
    }
    return null;
  },
};
