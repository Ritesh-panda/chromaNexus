import React from 'react';
import { FileQuestion } from 'lucide-react';
import { cn } from '@/utils/cn';

export interface EmptyStateProps {
  icon?: React.ReactNode;
  title: string;
  description: string;
  action?: React.ReactNode;
  className?: string;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  icon = <FileQuestion className="w-8 h-8 text-[#9CA3AF]" />,
  title,
  description,
  action,
  className,
}) => {
  return (
    <div className={cn('flex flex-col items-center justify-center p-10 text-center bg-white dark:bg-[#1B1E23] border border-dashed border-[#E5E7EB] dark:border-[#2F3540] rounded-2xl', className)}>
      <div className="p-3.5 rounded-2xl bg-[#F3F1ED] dark:bg-[#23272E] mb-3 text-[#1F2937] dark:text-[#F3F4F6]">{icon}</div>
      <h3 className="text-sm font-semibold text-[#1F2937] dark:text-[#F3F4F6]">{title}</h3>
      <p className="text-xs text-[#6B7280] dark:text-[#9CA3AF] max-w-sm mt-1 mb-5 leading-relaxed">{description}</p>
      {action && <div>{action}</div>}
    </div>
  );
};
