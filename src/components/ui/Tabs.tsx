import React from 'react';
import { cn } from '@/utils/cn';

export interface TabItem {
  id: string;
  label: string;
  icon?: React.ReactNode;
  badge?: string | number;
}

export interface TabsProps {
  tabs: TabItem[];
  activeTab: string;
  onChange: (id: string) => void;
  className?: string;
}

export const Tabs: React.FC<TabsProps> = ({ tabs, activeTab, onChange, className }) => {
  return (
    <div className={cn('flex items-center space-x-1 border-b border-[#E5E7EB] dark:border-[#2F3540] overflow-x-auto pb-px', className)}>
      {tabs.map((tab) => {
        const isActive = activeTab === tab.id;
        return (
          <button
            key={tab.id}
            onClick={() => onChange(tab.id)}
            className={cn(
              'flex items-center gap-2 px-3.5 py-2.5 text-xs sm:text-sm font-medium border-b-2 whitespace-nowrap transition-all duration-150',
              isActive
                ? 'border-[#10B981] text-[#1F2937] dark:text-[#F3F4F6] font-semibold'
                : 'border-transparent text-[#6B7280] hover:text-[#1F2937] dark:text-[#9CA3AF] dark:hover:text-[#F3F4F6] hover:border-[#D1D5DB]'
            )}
          >
            {tab.icon}
            <span>{tab.label}</span>
            {tab.badge !== undefined && (
              <span
                className={cn(
                  'ml-1 px-1.5 py-0.5 text-[10px] rounded-full font-medium',
                  isActive
                    ? 'bg-[#ECFDF5] text-[#15803D] dark:bg-emerald-950/40 dark:text-emerald-300'
                    : 'bg-[#F3F1ED] text-[#6B7280] dark:bg-[#23272E] dark:text-[#9CA3AF]'
                )}
              >
                {tab.badge}
              </span>
            )}
          </button>
        );
      })}
    </div>
  );
};
