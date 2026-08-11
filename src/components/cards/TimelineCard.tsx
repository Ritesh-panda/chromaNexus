import React from 'react';
import type { TimelineEvent } from '../../types';
import { Card } from '../ui/Card';
import { Badge } from '../ui/Badge';
import { Activity, Stethoscope, Pill, FileText, Hospital, ShieldAlert, Award } from 'lucide-react';

export interface TimelineCardProps {
  event: TimelineEvent;
  onSelect?: (event: TimelineEvent) => void;
}

export const TimelineCard: React.FC<TimelineCardProps> = ({ event, onSelect }) => {
  const getEventIcon = (type: TimelineEvent['type']) => {
    switch (type) {
      case 'diagnosis':
        return <Activity className="w-4 h-4 text-rose-500" />;
      case 'medication_start':
      case 'medication_stop':
        return <Pill className="w-4 h-4 text-emerald-500" />;
      case 'lab_test':
        return <FileText className="w-4 h-4 text-blue-500" />;
      case 'imaging':
        return <Stethoscope className="w-4 h-4 text-purple-500" />;
      case 'hospital_visit':
        return <Hospital className="w-4 h-4 text-amber-500" />;
      default:
        return <Award className="w-4 h-4 text-cyan-500" />;
    }
  };

  const getSeverityBadge = (severity?: TimelineEvent['severity']) => {
    if (!severity) return null;
    switch (severity) {
      case 'critical':
        return <Badge variant="danger">Critical</Badge>;
      case 'high':
        return <Badge variant="warning">High Priority</Badge>;
      case 'medium':
        return <Badge variant="default">Medium</Badge>;
      default:
        return <Badge variant="secondary">Routine</Badge>;
    }
  };

  return (
    <Card
      hoverEffect
      onClick={() => onSelect && onSelect(event)}
      className="cursor-pointer border-slate-200 dark:border-slate-800 p-5 space-y-3"
    >
      <div className="flex items-start justify-between">
        <div className="flex items-center space-x-3">
          <div className="p-2.5 rounded-xl bg-slate-100 dark:bg-slate-800/80 shrink-0">
            {getEventIcon(event.type)}
          </div>
          <div>
            <span className="text-xs font-mono font-medium text-blue-600 dark:text-blue-400">{event.date}</span>
            <h4 className="text-base font-semibold text-slate-900 dark:text-slate-100 leading-snug">{event.title}</h4>
          </div>
        </div>
        {getSeverityBadge(event.severity)}
      </div>

      <p className="text-xs text-slate-600 dark:text-slate-300 line-clamp-2 leading-relaxed">{event.description}</p>

      <div className="flex flex-wrap items-center justify-between gap-2 pt-2 text-xs border-t border-slate-100 dark:border-slate-800/60 text-slate-500 dark:text-slate-400">
        <div className="flex items-center space-x-2">
          {event.doctorName && <span>👨‍⚕️ {event.doctorName}</span>}
          {event.facility && <span className="opacity-75">📍 {event.facility}</span>}
        </div>
        {event.sourceReportTitle && (
          <span className="text-blue-600 dark:text-blue-400 font-medium hover:underline flex items-center gap-1">
            <FileText className="w-3 h-3" /> {event.sourceReportTitle}
          </span>
        )}
      </div>
    </Card>
  );
};
