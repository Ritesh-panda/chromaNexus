import React from 'react';
import { Card } from '../ui/Card';
import { cn } from '../../utils/cn';

export interface SummaryCardProps {
  title: string;
  icon?: React.ReactNode;
  badgeText?: string;
  children: React.ReactNode;
  className?: string;
}

export const SummaryCard: React.FC<SummaryCardProps> = ({ title, icon, badgeText, children, className }) => {
  return (
    <Card className={cn('p-6 space-y-4 border-slate-200 dark:border-slate-800', className)}>
      <div className="flex items-center justify-between pb-3 border-b border-slate-100 dark:border-slate-800/80">
        <div className="flex items-center space-x-2.5">
          {icon && <div className="p-2 rounded-xl bg-blue-50 dark:bg-blue-950/60 text-blue-600 dark:text-blue-400">{icon}</div>}
          <h3 className="text-base font-bold text-slate-900 dark:text-slate-100">{title}</h3>
        </div>
        {badgeText && (
          <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400">
            {badgeText}
          </span>
        )}
      </div>
      <div>{children}</div>
    </Card>
  );
};
