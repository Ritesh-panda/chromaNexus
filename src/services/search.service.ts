import { api } from './axios';
import { MOCK_REPORTS, MOCK_DISEASES, MOCK_MEDICATIONS, MOCK_TIMELINE_EVENTS } from '@/constants/mockData';
import type { MedicalReport, Disease, Medication, TimelineEvent } from '@/types';

export interface GlobalSearchResults {
  reports: MedicalReport[];
  diseases: Disease[];
  medications: Medication[];
  timelineEvents: TimelineEvent[];
}

export interface GlobalSearchResponse {
  query: string;
  totalMatches: number;
  results: GlobalSearchResults;
}

export const searchService = {
  async search(query: string): Promise<GlobalSearchResponse> {
    if (!query || !query.trim()) {
      return {
        query: '',
        totalMatches: 0,
        results: { reports: [], diseases: [], medications: [], timelineEvents: [] },
      };
    }

    try {
      const response = await api.get<GlobalSearchResponse>('/search', {
        params: { q: query.trim() },
      });
      if (response.data && response.data.results) {
        return response.data;
      }
    } catch {
      // Fallback to client-side search across mock data
    }

    const q = query.toLowerCase();
    const reports = MOCK_REPORTS.filter(
      (r) =>
        r.title.toLowerCase().includes(q) ||
        (r.summary && r.summary.toLowerCase().includes(q)) ||
        r.extractedEntities?.some((e) => e.name.toLowerCase().includes(q))
    );
    const diseases = MOCK_DISEASES.filter(
      (d) =>
        d.name.toLowerCase().includes(q) ||
        d.notes?.toLowerCase().includes(q) ||
        d.icdCode?.toLowerCase().includes(q)
    );
    const medications = MOCK_MEDICATIONS.filter(
      (m) =>
        m.name.toLowerCase().includes(q) ||
        (m.indication && m.indication.toLowerCase().includes(q))
    );
    const timelineEvents = MOCK_TIMELINE_EVENTS.filter(
      (t) =>
        t.title.toLowerCase().includes(q) ||
        t.description.toLowerCase().includes(q)
    );


    const totalMatches = reports.length + diseases.length + medications.length + timelineEvents.length;

    return {
      query,
      totalMatches,
      results: {
        reports,
        diseases,
        medications,
        timelineEvents,
      },
    };
  },
};
