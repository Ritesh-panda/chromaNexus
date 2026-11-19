import { api } from './axios';
import type { PatientKnowledgeGraphResponse, ClinicalCluster } from '@/types';

export const graphService = {
  async getPatientGraph(): Promise<PatientKnowledgeGraphResponse> {
    const response = await api.get<PatientKnowledgeGraphResponse>('/graph/patient');
    return response.data;
  },

  async getClusters(): Promise<ClinicalCluster[]> {
    const response = await api.get<ClinicalCluster[]>('/graph/clusters');
    return response.data;
  },

  async getGraphFacts(query: string): Promise<string[]> {
    const response = await api.get<string[]>('/graph/facts', {
      params: { query },
    });
    return response.data;
  },

  async syncGraph(): Promise<PatientKnowledgeGraphResponse> {
    const response = await api.post<PatientKnowledgeGraphResponse>('/graph/sync');
    return response.data;
  },
};

