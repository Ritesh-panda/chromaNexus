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


  async generatePdfSummary(): Promise<{ url: string; fileName: string }> {
    try {
      const response = await api.post<{ summary: DoctorSummary; downloadUrl: string }>('/summaries/generate');
      if (response.data && response.data.downloadUrl) {
        return {
          url: response.data.downloadUrl,
          fileName: 'ChronaNexus_Doctor_Summary_AlexVance_2026.pdf',
        };
      }
    } catch {
      // Fallback
    }
    await new Promise((resolve) => setTimeout(resolve, 800));
    return {
      url: '#',
      fileName: 'ChronaNexus_Doctor_Summary_AlexVance_2026.pdf',
    };
  },
};

