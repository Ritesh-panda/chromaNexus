import React from 'react';
import { Card } from '../ui/Card';
import { Badge } from '../ui/Badge';
import { FileText, Building2, User, Calendar, CheckCircle2, ShieldCheck } from 'lucide-react';
import type { MedicalReport } from '../../types';

export interface ReportCardProps {
  report: MedicalReport;
  onSelect?: (report: MedicalReport) => void;
}

export const ReportCard: React.FC<ReportCardProps> = ({ report, onSelect }) => {
  const getCategoryColor = (cat: MedicalReport['category']) => {
    switch (cat) {
      case 'blood_report': return 'bg-rose-500/10 text-rose-600 dark:text-rose-400';
      case 'mri': case 'ct_scan': return 'bg-purple-500/10 text-purple-600 dark:text-purple-400';
      case 'prescription': return 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400';
      case 'discharge_summary': return 'bg-amber-500/10 text-amber-600 dark:text-amber-400';
      default: return 'bg-blue-500/10 text-blue-600 dark:text-blue-400';
    }
  };

  return (
    <Card
      hoverEffect
      onClick={() => onSelect && onSelect(report)}
      className="cursor-pointer border-slate-200 dark:border-slate-800 p-5 space-y-3"
    >
      <div className="flex items-start justify-between">
        <div className="flex items-center space-x-3">
          <div className={`p-3 rounded-2xl shrink-0 ${getCategoryColor(report.category)}`}>
            <FileText className="w-5 h-5" />
          </div>
          <div>
            <h4 className="text-sm font-bold text-slate-900 dark:text-slate-100 line-clamp-1">{report.title}</h4>
            <p className="text-xs text-slate-400 font-mono mt-0.5">{report.fileName} • {(report.fileSize / 1024 / 1024).toFixed(1)} MB</p>
          </div>
        </div>
        <Badge variant={report.status === 'completed' ? 'success' : 'warning'}>
          {report.status}
        </Badge>
      </div>

      {report.summary && (
        <p className="text-xs text-slate-600 dark:text-slate-300 line-clamp-2 leading-relaxed bg-slate-50 dark:bg-slate-800/40 p-3 rounded-xl">
          {report.summary}
        </p>
      )}

      <div className="flex items-center justify-between text-xs text-slate-400 pt-2 border-t border-slate-100 dark:border-slate-800/60">
        <div className="flex items-center space-x-3">
          <span className="flex items-center gap-1"><Building2 className="w-3.5 h-3.5 text-slate-400" /> {report.hospitalName}</span>
          <span className="flex items-center gap-1"><Calendar className="w-3.5 h-3.5 text-slate-400" /> {report.reportDate}</span>
        </div>
        <span className="flex items-center gap-1 text-emerald-600 dark:text-emerald-400 font-medium">
          <ShieldCheck className="w-3.5 h-3.5" /> {(report.confidenceScore * 100).toFixed(0)}% AI Verified
        </span>
      </div>
    </Card>
  );
};
