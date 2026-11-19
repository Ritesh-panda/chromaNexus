import { api } from './axios';
import { MOCK_DOCTOR_SUMMARY } from '@/constants/mockData';
import type { DoctorSummary } from '@/types';

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

function getStoredUserName(): string {
  try {
    const saved = localStorage.getItem('chronanexus_auth_user');
    if (saved) {
      const u = JSON.parse(saved);
      return u?.name || 'Patient';
    }
  } catch {
    // Ignore
  }
  return 'Patient';
}

function createCleanDoctorSummary(): DoctorSummary {
  const patientName = getStoredUserName();
  return {
    patientName,
    age: undefined,
    gender: 'Not recorded',
    bloodGroup: 'Not recorded',
    primaryCarePhysician: 'Not assigned',
    generatedAt: new Date().toISOString(),
    summaryOverview: `${patientName}. Longitudinal medical intelligence digest grounded across indexed clinical records. Upload laboratory records, diagnostic imaging, or physician notes to compile your automated longitudinal doctor summary.`,
    currentDiseases: [],
    pastDiseases: [],
    activeMedications: [],
    historicalMedications: [],
    knownAllergies: [],
    abnormalLabs: [],
    recentLabs: [],
    proceduresAndImaging: [],
    riskFactors: [],
    recentReports: [],
    timelineHighlights: [],
    doctorQuestions: [
      'Review current health symptoms and diagnostic history.',
      'Discuss target reference ranges for any abnormal laboratory biomarkers.',
      'Evaluate necessity and timing of follow-up diagnostic imaging or procedures.'
    ],
    clinicianNotice: 'NOTICE TO CLINICIANS: This clinical digest was deterministically compiled from indexed medical documents on ChronaNexus. It provides longitudinal reference data and does not constitute an automated diagnosis, treatment recommendation, or prescribing directive. All findings must be clinically verified with original primary sources.'
  };
}

export const summaryService = {
  async getDoctorSummary(): Promise<DoctorSummary> {
    try {
      const response = await api.get<DoctorSummary>('/summaries/latest');
      if (response.data && response.data.summaryOverview) {
        return response.data;
      }
    } catch {
      // API error or no summary yet
    }
    if (isDemoUser()) {
      return MOCK_DOCTOR_SUMMARY;
    }
    return createCleanDoctorSummary();
  },

  async getSharedSummary(shareToken: string): Promise<DoctorSummary> {
    try {
      const response = await api.get<DoctorSummary>(`/summaries/share/${shareToken}`);
      if (response.data && response.data.summaryOverview) {
        return response.data;
      }
    } catch {
      // Fallback
    }
    return this.getDoctorSummary();
  },

  async generateDoctorSummary(): Promise<DoctorSummary> {
    try {
      const response = await api.post<DoctorSummary>('/summaries/generate');
      if (response.data && response.data.summaryOverview) {
        return response.data;
      }
    } catch {
      // Fallback
    }
    if (isDemoUser()) {
      return MOCK_DOCTOR_SUMMARY;
    }
    return createCleanDoctorSummary();
  },

  async updateDoctorQuestions(questions: string[]): Promise<DoctorSummary> {
    try {
      const response = await api.put<DoctorSummary>('/summaries/questions', { questions });
      return response.data;
    } catch {
      if (isDemoUser()) {
        return { ...MOCK_DOCTOR_SUMMARY, doctorQuestions: questions };
      }
      const clean = createCleanDoctorSummary();
      clean.doctorQuestions = questions;
      return clean;
    }
  },

  async generatePdfSummary(): Promise<{ url: string; fileName: string }> {
    try {
      const response = await api.post<{ summary: DoctorSummary; downloadUrl: string }>('/summaries/generate');
      if (response.data && response.data.downloadUrl) {
        return {
          url: response.data.downloadUrl,
          fileName: 'ChronaNexus_Doctor_Summary.pdf',
        };
      }
    } catch {
      // Fallback
    }
    return {
      url: '#',
      fileName: 'ChronaNexus_Doctor_Summary.pdf',
    };
  },
};
