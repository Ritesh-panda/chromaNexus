import React from 'react';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Pill, Activity, Calendar, UserCheck } from 'lucide-react';
import type { Disease, Medication } from '@/types';

export interface MedicalCardProps {
  item: Disease | Medication;
  type: 'disease' | 'medication';
}

export const MedicalCard: React.FC<MedicalCardProps> = ({ item, type }) => {
  if (type === 'disease') {
    const disease = item as Disease;
    return (
      <Card hoverEffect className="p-4 sm:p-5 space-y-2.5 border-[#E5E7EB] dark:border-[#2F3540] bg-white dark:bg-[#1B1E23]">
        <div className="flex items-start justify-between gap-3">
          <div className="flex items-center space-x-2.5">
            <div className="p-2 rounded-xl bg-[#FEF2F2] dark:bg-rose-950/30 text-[#B91C1C] dark:text-rose-400 shrink-0">
              <Activity className="w-4 h-4" />
            </div>
            <div>
              <h4 className="text-sm font-semibold text-[#1F2937] dark:text-[#F3F4F6]">{disease.name}</h4>
              {disease.icdCode && (
                <span className="text-[11px] font-mono text-[#9CA3AF] tabular-nums">ICD: {disease.icdCode}</span>
              )}
            </div>
          </div>
          <Badge
            variant={
              disease.status === 'active' || disease.status === 'chronic'
                ? 'warning'
                : disease.status === 'resolved'
                ? 'success'
                : 'secondary'
            }
          >
            {disease.status.replace('_', ' ')}
          </Badge>
        </div>
        {disease.notes && (
          <p className="text-xs text-[#6B7280] dark:text-[#9CA3AF] leading-relaxed pt-1">{disease.notes}</p>
        )}
        <div className="flex items-center justify-between text-[11px] text-[#6B7280] dark:text-[#9CA3AF] pt-2 border-t border-[#E5E7EB]/80 dark:border-[#2F3540]">
          <span className="flex items-center gap-1.5">
            <Calendar className="w-3 h-3 text-[#9CA3AF]" /> Diagnosed: {disease.diagnosedDate}
          </span>
          {disease.treatingDoctor && <span>{disease.treatingDoctor}</span>}
        </div>
      </Card>
    );
  }

  const med = item as Medication;
  return (
    <Card hoverEffect className="p-4 sm:p-5 space-y-2.5 border-[#E5E7EB] dark:border-[#2F3540] bg-white dark:bg-[#1B1E23]">
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center space-x-2.5">
          <div className="p-2 rounded-xl bg-[#ECFDF5] dark:bg-emerald-950/30 text-[#10B981] dark:text-emerald-400 shrink-0">
            <Pill className="w-4 h-4" />
          </div>
          <div>
            <h4 className="text-sm font-semibold text-[#1F2937] dark:text-[#F3F4F6]">{med.name}</h4>
            <span className="text-xs font-medium text-[#10B981] dark:text-emerald-400">
              {med.dosage} • {med.frequency}
            </span>
          </div>
        </div>
        <Badge variant={med.status === 'active' ? 'success' : 'secondary'}>{med.status}</Badge>
      </div>
      {med.indication && (
        <p className="text-xs text-[#6B7280] dark:text-[#9CA3AF] pt-1">
          Indication: <strong className="text-[#1F2937] dark:text-[#F3F4F6] font-medium">{med.indication}</strong>
        </p>
      )}
      <div className="flex items-center justify-between text-[11px] text-[#6B7280] dark:text-[#9CA3AF] pt-2 border-t border-[#E5E7EB]/80 dark:border-[#2F3540]">
        <span className="flex items-center gap-1.5">
          <Calendar className="w-3 h-3 text-[#9CA3AF]" /> Started: {med.startDate}
        </span>
        {med.prescribingDoctor && (
          <span className="flex items-center gap-1">
            <UserCheck className="w-3 h-3 text-[#9CA3AF]" /> {med.prescribingDoctor}
          </span>
        )}
      </div>
    </Card>
  );
};
