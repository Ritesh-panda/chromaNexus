import React from 'react';
import { Card } from '../ui/Card';
import { Badge } from '../ui/Badge';
import { Pill, Activity, Calendar, UserCheck } from 'lucide-react';
import type { Disease, Medication } from '../../types';

export interface MedicalCardProps {
  item: Disease | Medication;
  type: 'disease' | 'medication';
}

export const MedicalCard: React.FC<MedicalCardProps> = ({ item, type }) => {
  if (type === 'disease') {
    const disease = item as Disease;
    return (
      <Card hoverEffect className="p-5 space-y-2 border-slate-200 dark:border-slate-800">
        <div className="flex items-start justify-between">
          <div className="flex items-center space-x-2.5">
            <div className="p-2 rounded-xl bg-rose-100 dark:bg-rose-950/60 text-rose-600 dark:text-rose-400">
              <Activity className="w-4 h-4" />
            </div>
            <div>
              <h4 className="text-sm font-bold text-slate-900 dark:text-slate-100">{disease.name}</h4>
              {disease.icdCode && <span className="text-[11px] font-mono text-slate-400">ICD: {disease.icdCode}</span>}
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
        {disease.notes && <p className="text-xs text-slate-600 dark:text-slate-300 mt-2">{disease.notes}</p>}
        <div className="flex items-center justify-between text-[11px] text-slate-400 pt-2 border-t border-slate-100 dark:border-slate-800/60">
          <span className="flex items-center gap-1"><Calendar className="w-3 h-3" /> Diagnosed: {disease.diagnosedDate}</span>
          {disease.treatingDoctor && <span>{disease.treatingDoctor}</span>}
        </div>
      </Card>
    );
  }

  const med = item as Medication;
  return (
    <Card hoverEffect className="p-5 space-y-2 border-slate-200 dark:border-slate-800">
      <div className="flex items-start justify-between">
        <div className="flex items-center space-x-2.5">
          <div className="p-2 rounded-xl bg-emerald-100 dark:bg-emerald-950/60 text-emerald-600 dark:text-emerald-400">
            <Pill className="w-4 h-4" />
          </div>
          <div>
            <h4 className="text-sm font-bold text-slate-900 dark:text-slate-100">{med.name}</h4>
            <span className="text-xs font-semibold text-emerald-600 dark:text-emerald-400">{med.dosage} • {med.frequency}</span>
          </div>
        </div>
        <Badge variant={med.status === 'active' ? 'success' : 'secondary'}>{med.status}</Badge>
      </div>
      {med.indication && (
        <p className="text-xs text-slate-500 dark:text-slate-400">Indication: <strong className="text-slate-700 dark:text-slate-300">{med.indication}</strong></p>
      )}
      <div className="flex items-center justify-between text-[11px] text-slate-400 pt-2 border-t border-slate-100 dark:border-slate-800/60">
        <span className="flex items-center gap-1"><Calendar className="w-3 h-3" /> Started: {med.startDate}</span>
        {med.prescribingDoctor && <span className="flex items-center gap-1"><UserCheck className="w-3 h-3" /> {med.prescribingDoctor}</span>}
      </div>
    </Card>
  );
};
