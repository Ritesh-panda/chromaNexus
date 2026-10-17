import React from 'react';
import { AlertCircle, RotateCcw } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { cn } from '@/utils/cn';

export interface ErrorStateProps {
  title?: string;
  message?: string;
  onRetry?: () => void;
  className?: string;
}

export const ErrorState: React.FC<ErrorStateProps> = ({
  title = 'Unable to Load Data',
  message = 'An unexpected error occurred while processing patient information.',
  onRetry,
  className,
}) => {
  return (
    <div className={cn('flex flex-col items-center justify-center p-8 text-center bg-white dark:bg-[#1B1E23] border border-rose-200/80 dark:border-rose-900/40 rounded-2xl', className)}>
      <div className="p-3 rounded-2xl bg-[#FEF2F2] dark:bg-rose-950/30 text-[#B91C1C] dark:text-rose-400 mb-3">
        <AlertCircle className="w-6 h-6" />
      </div>
      <h3 className="text-sm font-semibold text-[#1F2937] dark:text-[#F3F4F6]">{title}</h3>
      <p className="text-xs text-[#6B7280] dark:text-[#9CA3AF] max-w-md mt-1 mb-4 leading-relaxed">{message}</p>
      {onRetry && (
        <Button variant="secondary" size="sm" onClick={onRetry} leftIcon={<RotateCcw className="w-3.5 h-3.5" />}>
          Try Again
        </Button>
      )}
    </div>
  );
};
