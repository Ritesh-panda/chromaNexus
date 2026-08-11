import React from 'react';
import { Loader2 } from 'lucide-react';
import { cn } from '../../utils/cn';

export interface LoadingProps {
  label?: string;
  className?: string;
  fullPage?: boolean;
}

export const Loading: React.FC<LoadingProps> = ({ label = 'Loading medical memory...', className, fullPage = false }) => {
  const content = (
    <div className={cn('flex flex-col items-center justify-center p-8 space-y-3', className)}>
      <div className="relative flex items-center justify-center">
        <div className="w-12 h-12 rounded-full border-2 border-blue-500/20 border-t-blue-600 animate-spin" />
        <Loader2 className="w-5 h-5 text-blue-600 absolute" />
      </div>
      <p className="text-xs font-semibold text-slate-500 dark:text-slate-400 tracking-wide animate-pulse">{label}</p>
    </div>
  );

  if (fullPage) {
    return <div className="min-h-screen w-full flex items-center justify-center bg-slate-50 dark:bg-[#0B0F19]">{content}</div>;
  }

  return content;
};
