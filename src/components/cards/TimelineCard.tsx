import React from 'react';
import type { TimelineEvent } from '@/types';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Activity, Stethoscope, Pill, FileText, Hospital, Award } from 'lucide-react';

export interface TimelineCardProps {
  event: TimelineEvent;
  onSelect?: (event: TimelineEvent) => void;
}

export const TimelineCard: React.FC<TimelineCardProps> = ({ event, onSelect }) => {
  const getEventIcon = (type: TimelineEvent['type']) => {
    switch (type) {
      case 'diagnosis':
        return <Activity className="w-4 h-4 text-[#B91C1C]" />;
      case 'medication_start':
      case 'medication_stop':
        return <Pill className="w-4 h-4 text-[#10B981]" />;
      case 'lab_test':
        return <FileText className="w-4 h-4 text-[#2563EB]" />;
      case 'imaging':
        return <Stethoscope className="w-4 h-4 text-[#4B5563]" />;
      case 'hospital_visit':
        return <Hospital className="w-4 h-4 text-[#B45309]" />;
      default:
        return <Award className="w-4 h-4 text-[#1F2937]" />;
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
      className="cursor-pointer border-[#E5E7EB] dark:border-[#2F3540] p-4 sm:p-5 space-y-2.5 bg-white dark:bg-[#1B1E23]"
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center space-x-3">
          <div className="p-2 rounded-xl bg-[#F3F1ED] dark:bg-[#23272E] border border-[#E5E7EB] dark:border-[#2F3540] shrink-0">
            {getEventIcon(event.type)}
          </div>
          <div>
            <span className="text-xs font-mono font-medium text-[#10B981] dark:text-emerald-400 tabular-nums">
              {event.date}
            </span>
            <h4 className="text-sm sm:text-base font-semibold text-[#1F2937] dark:text-[#F3F4F6] leading-snug">
              {event.title}
            </h4>
          </div>
        </div>
        {getSeverityBadge(event.severity)}
      </div>

      <p className="text-xs text-[#6B7280] dark:text-[#9CA3AF] line-clamp-2 leading-relaxed">
        {event.description}
      </p>

      <div className="flex flex-wrap items-center justify-between gap-2 pt-2 text-xs border-t border-[#E5E7EB]/80 dark:border-[#2F3540] text-[#6B7280] dark:text-[#9CA3AF]">
        <div className="flex items-center space-x-3">
          {event.doctorName && <span>👨‍⚕️ {event.doctorName}</span>}
          {event.facility && <span className="opacity-80">📍 {event.facility}</span>}
        </div>
        {event.sourceReportTitle && (
          <span className="text-[#10B981] dark:text-emerald-400 font-medium hover:underline flex items-center gap-1">
            <FileText className="w-3 h-3" /> {event.sourceReportTitle}
          </span>
        )}
      </div>
    </Card>
  );
};
