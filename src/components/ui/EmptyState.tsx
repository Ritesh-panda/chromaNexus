import React from 'react';
import { FileQuestion } from 'lucide-react';
import { cn } from '../../utils/cn';

export interface EmptyStateProps {
  icon?: React.ReactNode;
  title: string;
  description: string;
  action?: React.ReactNode;
  className?: string;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  icon = <FileQuestion className="w-10 h-10 text-slate-400" />,
  title,
  description,
  action,
  className,
}) => {
  return (
    <div className={cn('flex flex-col items-center justify-center p-12 text-center glass-card border border-dashed border-slate-300 dark:border-slate-800 rounded-2xl', className)}>
      <div className="p-4 rounded-full bg-slate-100 dark:bg-slate-800/80 mb-4">{icon}</div>
      <h3 className="text-base font-semibold text-slate-900 dark:text-slate-100">{title}</h3>
      <p className="text-xs text-slate-500 dark:text-slate-400 max-w-sm mt-1 mb-6">{description}</p>
      {action && <div>{action}</div>}
    </div>
  );
};
