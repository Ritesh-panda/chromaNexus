import React from 'react';
import { cva, type VariantProps } from 'class-variance-authority';
import { cn } from '@/utils/cn';

const badgeVariants = cva(
  'inline-flex items-center font-medium rounded-full px-2.5 py-0.5 text-xs transition-colors focus:outline-none',
  {
    variants: {
      variant: {
        default: 'bg-[#F3F1ED] text-[#1F2937] dark:bg-[#23272E] dark:text-[#F3F4F6] border border-[#E5E7EB] dark:border-[#2F3540]',
        secondary: 'bg-[#FAF8F5] text-[#6B7280] dark:bg-[#1B1E23] dark:text-[#9CA3AF] border border-[#E5E7EB] dark:border-[#2F3540]',
        success: 'bg-[#ECFDF5] text-[#15803D] dark:bg-emerald-950/40 dark:text-emerald-300 border border-emerald-200/70 dark:border-emerald-800/40',
        warning: 'bg-[#FFFBEB] text-[#B45309] dark:bg-amber-950/40 dark:text-amber-300 border border-amber-200/70 dark:border-amber-800/40',
        danger: 'bg-[#FEF2F2] text-[#B91C1C] dark:bg-rose-950/40 dark:text-rose-300 border border-rose-200/70 dark:border-rose-800/40',
        info: 'bg-[#EFF6FF] text-[#2563EB] dark:bg-blue-950/40 dark:text-blue-300 border border-blue-200/70 dark:border-blue-800/40',
        outline: 'border border-[#E5E7EB] dark:border-[#2F3540] text-[#1F2937] dark:text-[#F3F4F6] bg-transparent',
      },
    },
    defaultVariants: {
      variant: 'default',
    },
  }
);

export interface BadgeProps extends React.HTMLAttributes<HTMLDivElement>, VariantProps<typeof badgeVariants> {}

export const Badge: React.FC<BadgeProps> = ({ className, variant, children, ...props }) => {
  return (
    <div className={cn(badgeVariants({ variant }), className)} {...props}>
      {children}
    </div>
  );
};
