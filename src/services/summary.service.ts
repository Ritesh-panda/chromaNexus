import { api } from './axios';
import { MOCK_DOCTOR_SUMMARY } from '@/constants/mockData';
import type { DoctorSummary } from '@/types';

export const summaryService = {
  async getDoctorSummary(): Promise<DoctorSummary> {
    try {
      const response = await api.get<DoctorSummary>('/summaries/latest');
      if (response.data && response.data.summaryOverview) {
        return response.data;
      }
    } catch {
      // Graceful fallback to mock data
    }
    await new Promise((resolve) => setTimeout(resolve, 300));
    return MOCK_DOCTOR_SUMMARY;
  },

  async generateDoctorSummary(): Promise<DoctorSummary> {
    try {
      const response = await api.post<DoctorSummary>('/summaries/generate');
      if (response.data && response.data.summaryOverview) {
        return response.data;
      }
    } catch {
      // Graceful fallback
    }
    return MOCK_DOCTOR_SUMMARY;
  },

  async updateDoctorQuestions(questions: string[]): Promise<DoctorSummary> {
    try {
      const response = await api.put<DoctorSummary>('/summaries/questions', { questions });
      return response.data;
    } catch {
      return { ...MOCK_DOCTOR_SUMMARY, doctorQuestions: questions };
    }
  },

  async generatePdfSummary(): Promise<{ url: string; fileName: string }> {
    try {
      const response = await api.post<{ summary: DoctorSummary; downloadUrl: string }>('/summaries/generate');
      if (response.data && response.data.downloadUrl) {
        return {
          url: response.data.downloadUrl,
          fileName: 'ChronaNexus_Doctor_Summary_2026.pdf',
        };
      }
    } catch {
      // Fallback
    }
    await new Promise((resolve) => setTimeout(resolve, 500));
    return {
      url: '#',
      fileName: 'ChronaNexus_Doctor_Summary_2026.pdf',
    };
  },
};
