import React from 'react';
import type { TimelineEvent } from '@/types';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import {
  Activity,
  Stethoscope,
  Pill,
  FileText,
  Building2,
  Calendar,
  AlertTriangle,
  Upload,
  Clock,
  Layers,
} from 'lucide-react';

export interface TimelineCardProps {
  event: TimelineEvent;
  onSelect?: (event: TimelineEvent) => void;
  onReportClick?: (reportId: string) => void;
}

export const TimelineCard: React.FC<TimelineCardProps> = ({ event, onSelect, onReportClick }) => {
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
        return <Building2 className="w-4 h-4 text-[#B45309]" />;
      case 'medical_report':
        return <Layers className="w-4 h-4 text-[#059669]" />;
      default:
        return <Calendar className="w-4 h-4 text-[#1F2937]" />;
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
      className="cursor-pointer border-[#E5E7EB] dark:border-[#2F3540] p-4 sm:p-5 space-y-3 bg-white dark:bg-[#1B1E23] transition-all"
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-start space-x-3">
          <div className="p-2 rounded-xl bg-[#F3F1ED] dark:bg-[#23272E] border border-[#E5E7EB] dark:border-[#2F3540] shrink-0 mt-0.5">
            {getEventIcon(event.type)}
          </div>
          <div>
            <div className="flex items-center gap-2 flex-wrap">
              <span className={`text-xs font-mono font-medium ${event.isUnknownDate ? 'text-amber-600' : 'text-[#10B981] dark:text-emerald-400'} tabular-nums`}>
                {event.isUnknownDate ? 'Date Unknown' : event.date}
              </span>
              <span className="text-[10px] px-2 py-0.2 rounded-full bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 capitalize">
                {event.type.replace('_', ' ')}
              </span>
              {event.hasConflict && (
                <span className="text-[10px] px-1.5 py-0.2 rounded bg-amber-50 dark:bg-amber-950/40 text-amber-700 dark:text-amber-400 border border-amber-200/60 dark:border-amber-800/40 flex items-center gap-1">
                  <AlertTriangle className="w-2.5 h-2.5" /> Conflict
                </span>
              )}
            </div>
            <h4 className="text-sm sm:text-base font-semibold text-[#1F2937] dark:text-[#F3F4F6] leading-snug pt-0.5">
              {event.title}
            </h4>
          </div>
        </div>
        {getSeverityBadge(event.severity)}
      </div>

      <p className="text-xs text-[#6B7280] dark:text-[#9CA3AF] line-clamp-2 leading-relaxed">
        {event.description}
      </p>

      {/* Date metadata: Encounter Date vs Upload Date */}
      {event.uploadDate && (
        <div className="text-[10px] text-slate-500 dark:text-slate-400 flex items-center gap-1.5 pt-0.5">
          <Upload className="w-3 h-3 text-slate-400" />
          <span>Uploaded: {event.uploadDate.split('T')[0]}</span>
        </div>
      )}

      {/* Footer Info */}
      <div className="flex flex-wrap items-center justify-between gap-2 pt-2 text-xs border-t border-[#E5E7EB]/80 dark:border-[#2F3540] text-[#6B7280] dark:text-[#9CA3AF]">
        <div className="flex items-center space-x-3">
          {event.doctorName && (
            <span className="flex items-center gap-1">
              <Stethoscope className="w-3.5 h-3.5 text-slate-400" /> {event.doctorName}
            </span>
          )}
          {event.facility && (
            <span className="flex items-center gap-1">
              <Building2 className="w-3.5 h-3.5 text-slate-400" /> {event.facility}
            </span>
          )}
        </div>
        {event.sourceReportTitle && (
          <button
            type="button"
            onClick={(e) => {
              e.stopPropagation();
              if (onReportClick && event.sourceReportId) {
                onReportClick(event.sourceReportId);
              } else if (onSelect) {
                onSelect(event);
              }
            }}
            className="text-[#10B981] dark:text-emerald-400 font-medium hover:underline flex items-center gap-1"
          >
            <FileText className="w-3 h-3" /> {event.sourceReportTitle}
          </button>
        )}
      </div>
    </Card>
  );
};
