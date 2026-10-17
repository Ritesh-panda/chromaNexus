import React from 'react';
import { Card } from '@/components/ui/Card';
import { cn } from '@/utils/cn';

export interface SummaryCardProps {
  title: string;
  icon?: React.ReactNode;
  badgeText?: string;
  children: React.ReactNode;
  className?: string;
}

export const SummaryCard: React.FC<SummaryCardProps> = ({ title, icon, badgeText, children, className }) => {
  return (
    <Card className={cn('p-5 space-y-3.5 border-[#E5E7EB] dark:border-[#2F3540] bg-white dark:bg-[#1B1E23]', className)}>
      <div className="flex items-center justify-between pb-3 border-b border-[#E5E7EB]/80 dark:border-[#2F3540]">
        <div className="flex items-center space-x-2.5">
          {icon && (
            <div className="p-1.5 rounded-xl bg-[#F3F1ED] dark:bg-[#23272E] text-[#10B981]">
              {icon}
            </div>
          )}
          <h3 className="text-sm font-semibold text-[#1F2937] dark:text-[#F3F4F6]">{title}</h3>
        </div>
        {badgeText && (
          <span className="px-2 py-0.5 rounded-full text-[11px] font-medium bg-[#F3F1ED] dark:bg-[#23272E] text-[#6B7280] dark:text-[#9CA3AF] border border-[#E5E7EB] dark:border-[#2F3540]">
            {badgeText}
          </span>
        )}
      </div>
      <div>{children}</div>
    </Card>
  );
};
