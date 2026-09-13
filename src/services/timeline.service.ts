import { MOCK_TIMELINE_EVENTS } from '@/constants/mockData';
import type { TimelineEvent } from '@/types';

export const timelineService = {
  async getTimelineEvents(filterType?: string): Promise<TimelineEvent[]> {
    await new Promise((resolve) => setTimeout(resolve, 500));
    let events = [...MOCK_TIMELINE_EVENTS];
    if (filterType && filterType !== 'all') {
      events = events.filter((e) => e.type === filterType);
    }
    return events.sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime());
  },
};
