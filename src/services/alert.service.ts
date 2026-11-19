import { api } from './axios';

export interface HealthAlert {
  id: string;
  title: string;
  category: string;
  severity: 'low' | 'medium' | 'high';
  source: string;
  date: string;
  summary: string;
  link: string;
}

interface HealthAlertResponse {
  status: string;
  count: number;
  alerts: HealthAlert[];
}

export const alertService = {
  async getHealthAlerts(): Promise<HealthAlert[]> {
    try {
      const response = await api.get<HealthAlertResponse>('/alerts');
      return response.data?.alerts || [];
    } catch (error) {
      console.warn('Alert service error, using local fallback:', error);
      return [
        {
          id: 'alert_1',
          title: 'MoHFW Advisory: Hydration & Glycemic Control During Illness',
          category: 'Chronic Disease Advisory',
          severity: 'medium',
          source: 'Ministry of Health & Family Welfare (MoHFW)',
          date: 'Active Clinical Alert',
          summary: 'Patients diagnosed with Type 2 Diabetes should monitor blood glucose frequently during fever. Adequate hydration with sugar-free fluids is critical.',
          link: 'https://www.mohfw.gov.in/'
        },
        {
          id: 'alert_2',
          title: 'WHO Epidemic Alert: Seasonal Respiratory & Viral Infection Vigilance',
          category: 'Epidemic Surveillance',
          severity: 'high',
          source: 'World Health Organization (WHO)',
          date: 'Active Surveillance',
          summary: 'Maintain hygienic precautions, report persistent fever (>102°F) or acute breathlessness promptly, and seek clinic evaluation.',
          link: 'https://www.who.int/emergencies/disease-outbreak-news'
        }
      ];
    }
  }
};
