import { api } from './axios';
import { MOCK_TIMELINE_EVENTS } from '@/constants/mockData';
import type { TimelineEvent } from '@/types';

export const timelineService = {
  async getTimelineEvents(filterType?: string): Promise<TimelineEvent[]> {
    try {
      const params: Record<string, string> = {};
      if (filterType && filterType !== 'all') {
        params.event_type = filterType;
      }
      const response = await api.get<TimelineEvent[]>('/timeline', { params });
      if (response.data && Array.isArray(response.data) && response.data.length > 0) {
        return response.data;
      }
    } catch {
      // Graceful fallback to mock data
    }

    let events = [...MOCK_TIMELINE_EVENTS];
    if (filterType && filterType !== 'all') {
      events = events.filter((e) => e.type === filterType);
    }
    return events.sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime());
  },
};

