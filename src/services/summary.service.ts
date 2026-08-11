import { MOCK_DOCTOR_SUMMARY } from '../constants/mockData';
import { DoctorSummary } from '../types';

export const summaryService = {
  async getDoctorSummary(): Promise<DoctorSummary> {
    await new Promise((resolve) => setTimeout(resolve, 600));
    return MOCK_DOCTOR_SUMMARY;
  },

  async generatePdfSummary(): Promise<{ url: string; fileName: string }> {
    await new Promise((resolve) => setTimeout(resolve, 1000));
    return {
      url: '#',
      fileName: 'ChronaNexus_Doctor_Summary_AlexVance_2026.pdf',
    };
  },
};
