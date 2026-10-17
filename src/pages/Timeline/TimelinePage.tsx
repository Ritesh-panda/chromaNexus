import React, { useEffect, useState } from 'react';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { timelineService } from '@/services/timeline.service';
import { MOCK_TIMELINE_EVENTS } from '@/constants/mockData';
import type { TimelineEvent } from '@/types';
import { Modal } from '@/components/ui/Modal';
import {
  GitCommit,
  Filter,
  FileText,
  Building2,
  Activity,
  Pill,
  ChevronRight,
  Stethoscope
} from 'lucide-react';

export const TimelinePage: React.FC = () => {
  const [selectedType, setSelectedType] = useState<string>('all');
  const [selectedYear, setSelectedYear] = useState<string>('all');
  const [selectedEvent, setSelectedEvent] = useState<TimelineEvent | null>(null);
  const [events, setEvents] = useState<TimelineEvent[]>([]);

  useEffect(() => {
    let isMounted = true;
    const fetchTimeline = async () => {
      try {
        const data = await timelineService.getTimelineEvents(selectedType);
        if (isMounted) {
          setEvents(data && data.length > 0 ? data : MOCK_TIMELINE_EVENTS);
        }
      } catch {
        if (isMounted) {
          setEvents(MOCK_TIMELINE_EVENTS);
        }
      }
    };
    fetchTimeline();
    return () => {
      isMounted = false;
    };
  }, [selectedType]);

  const eventTypes = [
    { id: 'all', label: 'All Categories' },
    { id: 'diagnosis', label: 'Diagnoses' },
    { id: 'medication_start', label: 'Medications' },
    { id: 'lab_test', label: 'Lab Tests' },
    { id: 'imaging', label: 'Imaging / MRI' },
    { id: 'hospital_visit', label: 'Consultations' },
  ];

  const filteredEvents = events.filter((e) => {
    const matchesType =
      selectedType === 'all'
        ? true
        : selectedType === 'medication_start'
        ? e.type === 'medication_start' || e.type === 'medication_stop'
        : e.type === selectedType;
    const matchesYear = selectedYear === 'all' || e.year.toString() === selectedYear;
    return matchesType && matchesYear;
  });

  const availableYears = Array.from(new Set(events.map((e) => e.year))).sort((a, b) => b - a);
  const displayedYears = Array.from(new Set(filteredEvents.map((e) => e.year))).sort((a, b) => b - a);

  const getEventIcon = (type: string) => {
    switch (type) {
      case 'diagnosis':
        return <Activity className="w-4 h-4 text-[#B91C1C]" />;
      case 'medication_start':
      case 'medication_stop':
        return <Pill className="w-4 h-4 text-[#10B981]" />;
      case 'hospital_visit':
        return <Stethoscope className="w-4 h-4 text-[#2563EB]" />;
      default:
        return <FileText className="w-4 h-4 text-[#4B5563]" />;
    }
  };

  return (
    <div className="space-y-6 sm:space-y-8 pb-12">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl sm:text-2xl font-semibold text-[#1F2937] dark:text-[#F3F4F6] flex items-center gap-2">
            <GitCommit className="w-5 h-5 text-[#10B981]" /> Longitudinal Medical Timeline
          </h1>
          <p className="text-xs text-[#6B7280] dark:text-[#9CA3AF] mt-0.5">
            Chronological record of diagnoses, transitions, prescriptions, and clinical encounters (2019 - 2026).
          </p>
        </div>

        <div className="flex items-center space-x-2">
          <Badge variant="success">Auto-Constructed Trajectory</Badge>
          <span className="text-xs text-[#6B7280] dark:text-[#9CA3AF] font-mono tabular-nums">
            {filteredEvents.length} milestones
          </span>
        </div>
      </div>

      {/* Year Scrubber / Fast Jump Strip */}
      <div className="bg-white dark:bg-[#1B1E23] p-3 rounded-2xl border border-[#E5E7EB] dark:border-[#2F3540] shadow-[0_1px_2px_0_rgba(0,0,0,0.02)] space-y-3">
        <div className="flex items-center justify-between text-xs text-[#6B7280] dark:text-[#9CA3AF] px-1">
          <span className="font-semibold uppercase tracking-wider text-[10px] text-[#9CA3AF]">Timeline Year Scrubber</span>
          <span>Jump to historical period</span>
        </div>
        <div className="flex items-center gap-2 overflow-x-auto pb-1">
          <button
            onClick={() => setSelectedYear('all')}
            className={`px-3.5 py-1.5 rounded-xl text-xs font-medium whitespace-nowrap transition-colors ${
              selectedYear === 'all'
                ? 'bg-[#1F2937] text-white dark:bg-[#10B981] dark:text-white shadow-sm'
                : 'bg-[#FAF8F5] dark:bg-[#23272E] text-[#6B7280] dark:text-[#9CA3AF] hover:bg-[#F3F1ED] dark:hover:bg-[#2D323B]'
            }`}
          >
            All Years (2019-2026)
          </button>
          {availableYears.map((yr) => (
            <button
              key={yr}
              onClick={() => setSelectedYear(yr.toString())}
              className={`px-3.5 py-1.5 rounded-xl text-xs font-mono font-medium whitespace-nowrap transition-colors tabular-nums ${
                selectedYear === yr.toString()
                  ? 'bg-[#10B981] text-white shadow-sm font-semibold'
                  : 'bg-[#FAF8F5] dark:bg-[#23272E] text-[#6B7280] dark:text-[#9CA3AF] hover:bg-[#F3F1ED] dark:hover:bg-[#2D323B]'
              }`}
            >
              {yr}
            </button>
          ))}
        </div>
      </div>

      {/* Filter Tabs Strip */}
      <div className="bg-white dark:bg-[#1B1E23] p-2 sm:p-2.5 rounded-2xl border border-[#E5E7EB] dark:border-[#2F3540] flex items-center space-x-1.5 overflow-x-auto shadow-[0_1px_2px_0_rgba(0,0,0,0.02)]">
        <Filter className="w-3.5 h-3.5 text-[#9CA3AF] ml-2 shrink-0" />
        {eventTypes.map((t) => (
          <button
            key={t.id}
            onClick={() => setSelectedType(t.id)}
            className={`px-3 py-1.5 rounded-xl text-xs font-medium whitespace-nowrap transition-colors ${
              selectedType === t.id
                ? 'bg-[#1F2937] text-white dark:bg-[#10B981] dark:text-white shadow-sm'
                : 'text-[#6B7280] dark:text-[#9CA3AF] hover:bg-[#F3F1ED] dark:hover:bg-[#23272E]'
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {/* Vertical Longitudinal Timeline Stream */}
      {displayedYears.length === 0 ? (
        <div className="p-12 text-center bg-white dark:bg-[#1B1E23] rounded-2xl border border-[#E5E7EB] dark:border-[#2F3540] space-y-3">
          <GitCommit className="w-8 h-8 text-[#9CA3AF] mx-auto opacity-50" />
          <h3 className="text-base font-semibold text-[#1F2937] dark:text-[#F3F4F6]">No Milestones Found</h3>
          <p className="text-xs text-[#6B7280] dark:text-[#9CA3AF]">
            No clinical records matched the selected year and category filters.
          </p>
          <Button variant="secondary" size="sm" onClick={() => { setSelectedType('all'); setSelectedYear('all'); }}>
            Reset Filters
          </Button>
        </div>
      ) : (
        <div className="relative pl-6 sm:pl-10 space-y-12 border-l-2 border-[#E5E7EB] dark:border-[#2F3540] ml-4 sm:ml-6">
          {displayedYears.map((yr) => {
            const eventsInYr = filteredEvents.filter((e) => e.year === yr);
            return (
              <div key={yr} className="space-y-4 relative">
                {/* Year Marker Badge */}
                <div className="absolute -left-[31px] sm:-left-[47px] top-0 flex items-center space-x-3">
                  <div className="w-8 h-8 sm:w-9 sm:h-9 rounded-full bg-white dark:bg-[#1B1E23] border-2 border-[#10B981] text-[#1F2937] dark:text-[#F3F4F6] font-semibold text-xs sm:text-sm flex items-center justify-center shadow-sm tabular-nums ring-4 ring-[#FAF8F5] dark:ring-[#121417]">
                    {yr}
                  </div>
                </div>

                <div className="pt-1 pl-3 sm:pl-4 space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-[11px] font-semibold text-[#6B7280] dark:text-[#9CA3AF] tracking-wider uppercase tabular-nums">
                      {yr} Clinical Records ({eventsInYr.length})
                    </span>
                  </div>

                  <div className="space-y-3">
                    {eventsInYr.map((event) => (
                      <div
                        key={event.id}
                        onClick={() => setSelectedEvent(event)}
                        className="p-4 sm:p-5 rounded-2xl bg-white dark:bg-[#1B1E23] border border-[#E5E7EB] dark:border-[#2F3540] hover:border-[#10B981]/50 cursor-pointer transition-all shadow-[0_1px_2px_0_rgba(0,0,0,0.02)] group flex flex-col sm:flex-row sm:items-center justify-between gap-3"
                      >
                        <div className="flex items-start gap-3.5 min-w-0">
                          <div className="p-2.5 rounded-xl bg-[#FAF8F5] dark:bg-[#23272E] border border-[#E5E7EB] dark:border-[#2F3540] shrink-0 mt-0.5">
                            {getEventIcon(event.type)}
                          </div>
                          <div className="min-w-0 space-y-1">
                            <div className="flex items-center gap-2 flex-wrap">
                              <span className="text-xs font-mono font-semibold text-[#10B981] tabular-nums">
                                {event.date}
                              </span>
                              <Badge variant="secondary" className="text-[10px] py-0">{event.type.replace('_', ' ')}</Badge>
                              {event.facility && (
                                <span className="text-[11px] text-[#6B7280] dark:text-[#9CA3AF] flex items-center gap-1">
                                  <Building2 className="w-3 h-3" /> {event.facility}
                                </span>
                              )}
                            </div>
                            <h4 className="text-sm font-semibold text-[#1F2937] dark:text-[#F3F4F6] group-hover:text-[#10B981] transition-colors">
                              {event.title}
                            </h4>
                            <p className="text-xs text-[#6B7280] dark:text-[#9CA3AF] leading-relaxed line-clamp-2">
                              {event.description}
                            </p>
                          </div>
                        </div>

                        <div className="flex items-center gap-2 shrink-0 self-end sm:self-center">
                          <span className="text-xs text-[#10B981] font-medium hidden sm:inline-flex items-center gap-1 group-hover:translate-x-0.5 transition-transform">
                            Clinical Context <ChevronRight className="w-3.5 h-3.5" />
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Event Inspection Modal */}
      {selectedEvent && (
        <Modal
          isOpen={!!selectedEvent}
          onClose={() => setSelectedEvent(null)}
          title={selectedEvent.title}
          description={`Recorded: ${selectedEvent.date} • Facility: ${selectedEvent.facility || 'Verified Health Record'}`}
        >
          <div className="space-y-4 pt-1">
            <div className="p-4 rounded-xl bg-[#FAF8F5] dark:bg-[#23272E]/50 border border-[#E5E7EB] dark:border-[#2F3540] space-y-1.5">
              <span className="text-[10px] font-semibold text-[#6B7280] dark:text-[#9CA3AF] uppercase tracking-wider">
                Clinical Context & Narrative
              </span>
              <p className="text-xs text-[#4B5563] dark:text-[#D1D5DB] leading-relaxed">{selectedEvent.description}</p>
            </div>

            {selectedEvent.connectedEntities && (
              <div className="space-y-2">
                <span className="text-[10px] font-semibold uppercase tracking-wider text-[#6B7280] dark:text-[#9CA3AF]">
                  Connected Clinical Entities
                </span>
                {selectedEvent.connectedEntities.diseases && (
                  <div className="flex flex-wrap gap-1.5">
                    {selectedEvent.connectedEntities.diseases.map((d, idx) => (
                      <Badge key={idx} variant="danger">Diagnosed: {d}</Badge>
                    ))}
                  </div>
                )}
                {selectedEvent.connectedEntities.medications && (
                  <div className="flex flex-wrap gap-1.5">
                    {selectedEvent.connectedEntities.medications.map((m, idx) => (
                      <Badge key={idx} variant="success">Prescribed: {m}</Badge>
                    ))}
                  </div>
                )}
              </div>
            )}

            {selectedEvent.sourceReportTitle && (
              <div className="p-3 rounded-xl bg-[#FAF8F5] dark:bg-[#23272E]/60 border border-[#E5E7EB] dark:border-[#2F3540] flex items-center justify-between text-xs">
                <span className="font-medium text-[#1F2937] dark:text-[#F3F4F6] flex items-center gap-1.5">
                  <FileText className="w-3.5 h-3.5 text-[#10B981]" /> {selectedEvent.sourceReportTitle}
                </span>
                <span className="text-[#10B981] font-medium text-[11px]">Cited Record</span>
              </div>
            )}

            <Button variant="primary" className="w-full mt-2" onClick={() => setSelectedEvent(null)}>
              Close
            </Button>
          </div>
        </Modal>
      )}
    </div>
  );
};
