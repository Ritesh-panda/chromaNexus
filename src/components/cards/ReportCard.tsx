import React from 'react';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { FileText, Building2, Calendar, ShieldCheck } from 'lucide-react';
import type { MedicalReport } from '@/types';

export interface ReportCardProps {
  report: MedicalReport;
  onSelect?: (report: MedicalReport) => void;
}

export const ReportCard: React.FC<ReportCardProps> = ({ report, onSelect }) => {
  return (
    <Card
      hoverEffect
      onClick={() => onSelect && onSelect(report)}
      className="cursor-pointer border-[#E5E7EB] dark:border-[#2F3540] p-4 sm:p-5 space-y-3 bg-white dark:bg-[#1B1E23]"
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center space-x-3 min-w-0">
          <div className="p-2.5 rounded-xl bg-[#F3F1ED] dark:bg-[#23272E] text-[#1F2937] dark:text-[#F3F4F6] shrink-0 border border-[#E5E7EB] dark:border-[#2F3540]">
            <FileText className="w-4 h-4 text-[#10B981]" />
          </div>
          <div className="min-w-0">
            <h4 className="text-sm font-semibold text-[#1F2937] dark:text-[#F3F4F6] truncate">{report.title}</h4>
            <p className="text-xs text-[#6B7280] dark:text-[#9CA3AF] font-mono mt-0.5 tabular-nums">
              {report.fileName} • {(report.fileSize / 1024 / 1024).toFixed(1)} MB
            </p>
          </div>
        </div>
        <Badge variant={report.status === 'completed' ? 'success' : 'warning'} className="shrink-0">
          {report.status}
        </Badge>
      </div>

      {report.summary && (
        <p className="text-xs text-[#4B5563] dark:text-[#D1D5DB] line-clamp-2 leading-relaxed bg-[#FAF8F5] dark:bg-[#23272E]/50 border border-[#E5E7EB]/70 dark:border-[#2F3540] p-3 rounded-xl">
          {report.summary}
        </p>
      )}

      <div className="flex flex-wrap items-center justify-between gap-2 text-xs text-[#6B7280] dark:text-[#9CA3AF] pt-2 border-t border-[#E5E7EB]/80 dark:border-[#2F3540]">
        <div className="flex items-center space-x-3">
          <span className="flex items-center gap-1.5">
            <Building2 className="w-3.5 h-3.5 text-[#9CA3AF]" /> {report.hospitalName}
          </span>
          <span className="flex items-center gap-1.5">
            <Calendar className="w-3.5 h-3.5 text-[#9CA3AF]" /> {report.reportDate}
          </span>
        </div>
        <span className="flex items-center gap-1 text-[#15803D] dark:text-emerald-400 font-medium text-[11px]">
          <ShieldCheck className="w-3.5 h-3.5" /> {(report.confidenceScore * 100).toFixed(0)}% AI Verified
        </span>
      </div>
    </Card>
  );
};
