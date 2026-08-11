import React, { useState } from 'react';
import { Card } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { Badge } from '../../components/ui/Badge';
import { MOCK_TIMELINE_EVENTS } from '../../constants/mockData';
import { TimelineEvent, TimelineEventType } from '../../types';
import { TimelineCard } from '../../components/cards/TimelineCard';
import { Modal } from '../../components/ui/Modal';
import { GitCommit, Filter, Calendar, Activity, Sparkles, FileText, ChevronRight } from 'lucide-react';

export const TimelinePage: React.FC = () => {
  const [selectedType, setSelectedType] = useState<string>('all');
  const [selectedEvent, setSelectedEvent] = useState<TimelineEvent | null>(null);

  const eventTypes = [
    { id: 'all', label: 'All Events' },
    { id: 'diagnosis', label: 'Diagnoses' },
    { id: 'medication_start', label: 'Medication Changes' },
    { id: 'lab_test', label: 'Lab Tests' },
    { id: 'imaging', label: 'Imaging / MRI' },
    { id: 'hospital_visit', label: 'Hospital Visits' },
  ];

  const filteredEvents = MOCK_TIMELINE_EVENTS.filter((e) => {
    if (selectedType === 'all') return true;
    if (selectedType === 'medication_start') return e.type === 'medication_start' || e.type === 'medication_stop';
    return e.type === selectedType;
  });

  // Group events by Year
  const years = Array.from(new Set(filteredEvents.map((e) => e.year))).sort((a, b) => b - a);

  return (
    <div className="space-y-8 pb-12">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-extrabold text-slate-900 dark:text-slate-100 flex items-center gap-2">
            <GitCommit className="w-6 h-6 text-purple-500" /> Longitudinal Medical Timeline
          </h1>
          <p className="text-xs text-slate-500 dark:text-slate-400">
            Automatically constructed timeline of diagnoses, surgeries, medications, and clinical events (2019 - 2026).
          </p>
        </div>

        <div className="flex items-center space-x-2">
          <Badge variant="success">Auto-Reasoning Connected</Badge>
        </div>
      </div>

      {/* Filter Tabs */}
      <div className="glass-card p-3 rounded-2xl border border-slate-200 dark:border-slate-800 flex items-center space-x-2 overflow-x-auto">
        <Filter className="w-4 h-4 text-slate-400 ml-2 shrink-0" />
        {eventTypes.map((t) => (
          <button
            key={t.id}
            onClick={() => setSelectedType(t.id)}
            className={`px-3.5 py-1.5 rounded-xl text-xs font-semibold whitespace-nowrap transition-all ${
              selectedType === t.id
                ? 'bg-purple-600 text-white shadow-md shadow-purple-500/20'
                : 'text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800'
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {/* Vertical Interactive Longitudinal Timeline */}
      <div className="relative pl-6 sm:pl-10 space-y-12 border-l-2 border-purple-500/30 dark:border-purple-500/20 ml-4 sm:ml-6">
        {years.map((yr) => {
          const eventsInYr = filteredEvents.filter((e) => e.year === yr);
          return (
            <div key={yr} className="space-y-6 relative">
              {/* Year Marker Pill */}
              <div className="absolute -left-[31px] sm:-left-[47px] top-0 flex items-center space-x-3">
                <div className="w-8 h-8 sm:w-10 sm:h-10 rounded-full bg-purple-600 text-white font-extrabold text-xs sm:text-sm flex items-center justify-center shadow-lg ring-4 ring-slate-50 dark:ring-[#0B0F19]">
                  {yr}
                </div>
              </div>

              <div className="pt-1.5 pl-4 sm:pl-6 space-y-4">
                <span className="text-xs font-bold text-purple-600 dark:text-purple-400 tracking-wider uppercase">
                  {yr} Milestones ({eventsInYr.length})
                </span>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {eventsInYr.map((event) => (
                    <TimelineCard key={event.id} event={event} onSelect={(e) => setSelectedEvent(e)} />
                  ))}
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Event Inspection Modal */}
      {selectedEvent && (
        <Modal
          isOpen={!!selectedEvent}
          onClose={() => setSelectedEvent(null)}
          title={selectedEvent.title}
          description={`Logged Date: ${selectedEvent.date} • Facility: ${selectedEvent.facility || 'Verified Health Record'}`}
        >
          <div className="space-y-4 pt-2">
            <div className="p-4 rounded-2xl bg-purple-50/40 dark:bg-purple-950/20 border border-purple-200/50 dark:border-purple-800/40 space-y-2">
              <span className="text-xs font-bold text-purple-600 dark:text-purple-400 uppercase">Milestone Context</span>
              <p className="text-xs text-slate-700 dark:text-slate-300 leading-relaxed">{selectedEvent.description}</p>
            </div>

            {selectedEvent.connectedEntities && (
              <div className="space-y-2">
                <span className="text-xs font-bold text-slate-400 uppercase">Connected Medical Entities</span>
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
              <div className="p-3 rounded-xl bg-slate-100 dark:bg-slate-800/60 flex items-center justify-between text-xs">
                <span className="font-semibold text-slate-700 dark:text-slate-300 flex items-center gap-1.5">
                  <FileText className="w-4 h-4 text-blue-500" /> {selectedEvent.sourceReportTitle}
                </span>
                <span className="text-blue-600 font-bold">Cited Record</span>
              </div>
            )}

            <Button variant="primary" className="w-full mt-2" onClick={() => setSelectedEvent(null)}>
              Close Timeline Detail
            </Button>
          </div>
        </Modal>
      )}
    </div>
  );
};
