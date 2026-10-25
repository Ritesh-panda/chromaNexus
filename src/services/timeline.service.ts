import { api } from './axios';
import { MOCK_TIMELINE_EVENTS } from '@/constants/mockData';
import type { TimelineEvent, TimelineSummary } from '@/types';

export interface TimelineQueryParams {
  filterType?: string;
  facility?: string;
  startDate?: string;
  endDate?: string;
  year?: number;
  order?: 'asc' | 'desc';
}

export const timelineService = {
  async getTimelineEvents(params?: TimelineQueryParams | string): Promise<TimelineEvent[]> {
    try {
      const qParams: Record<string, any> = {};
      if (typeof params === 'string') {
        if (params && params !== 'all') {
          qParams.event_type = params;
        }
      } else if (params) {
        if (params.filterType && params.filterType !== 'all') {
          qParams.event_type = params.filterType;
        }
        if (params.facility && params.facility !== 'all') {
          qParams.facility = params.facility;
        }
        if (params.startDate) {
          qParams.start_date = params.startDate;
        }
        if (params.endDate) {
          qParams.end_date = params.endDate;
        }
        if (params.year) {
          qParams.year = params.year;
        }
        if (params.order) {
          qParams.order = params.order;
        }
      }

      const response = await api.get<TimelineEvent[]>('/timeline', { params: qParams });
      if (response.data && Array.isArray(response.data)) {
        return response.data;
      }
    } catch (err) {
      console.warn('Timeline API request encountered an issue:', err);
    }

    // Fallback if offline / demo mode
    let events = [...MOCK_TIMELINE_EVENTS];
    const filterType = typeof params === 'string' ? params : params?.filterType;
    if (filterType && filterType !== 'all') {
      events = events.filter((e) => e.type === filterType);
    }
    return events.sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime());
  },

  async getTimelineFacilities(): Promise<string[]> {
    try {
      const response = await api.get<{ facilities: string[] }>('/timeline/facilities');
      if (response.data?.facilities) {
        return response.data.facilities;
      }
    } catch (err) {
      console.warn('Timeline facilities API request encountered an issue:', err);
    }
    // Extract from mock data
    const set = new Set<string>();
    MOCK_TIMELINE_EVENTS.forEach((e) => {
      if (e.facility) set.add(e.facility);
    });
    return Array.from(set).sort();
  },

  async getTimelineSummary(): Promise<TimelineSummary | null> {
    try {
      const response = await api.get<TimelineSummary>('/timeline/summary');
      if (response.data) {
        return response.data;
      }
    } catch (err) {
      console.warn('Timeline summary API request encountered an issue:', err);
    }
    return null;
  },
};
