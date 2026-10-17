import React from 'react';
import { cva, type VariantProps } from 'class-variance-authority';
import { cn } from '@/utils/cn';
import { Loader2 } from 'lucide-react';

const buttonVariants = cva(
  'inline-flex items-center justify-center font-medium rounded-xl transition-all duration-150 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-1 disabled:opacity-45 disabled:cursor-not-allowed select-none active:scale-[0.98]',
  {
    variants: {
      variant: {
        primary: 'bg-[#10B981] hover:bg-[#059669] text-white shadow-sm hover:shadow focus-visible:ring-emerald-500/25',
        secondary: 'bg-white text-[#1F2937] border border-[#E5E7EB] hover:bg-[#F3F1ED] hover:border-[#D1D5DB] shadow-sm dark:bg-[#1B1E23] dark:text-[#F3F4F6] dark:border-[#2F3540] dark:hover:bg-[#23272E] focus-visible:ring-neutral-400',
        outline: 'border border-[#E5E7EB] bg-transparent text-[#1F2937] hover:bg-[#FAF8F5] dark:border-[#2F3540] dark:text-[#F3F4F6] dark:hover:bg-[#23272E] focus-visible:ring-neutral-400',
        ghost: 'bg-transparent text-[#6B7280] hover:text-[#1F2937] hover:bg-[#F3F1ED] dark:text-[#9CA3AF] dark:hover:text-[#F3F4F6] dark:hover:bg-[#23272E] focus-visible:ring-neutral-400',
        danger: 'bg-[#B91C1C] hover:bg-[#991B1B] text-white shadow-sm focus-visible:ring-rose-500/25',
        success: 'bg-[#15803D] hover:bg-[#166534] text-white shadow-sm focus-visible:ring-emerald-600/25',
      },
      size: {
        sm: 'h-8 px-3 text-xs gap-1.5',
        md: 'h-9 px-4 text-xs sm:text-sm gap-2',
        lg: 'h-11 px-5 text-sm sm:text-base gap-2.5',
        icon: 'h-9 w-9 p-0 rounded-xl',
      },
    },
    defaultVariants: {
      variant: 'primary',
      size: 'md',
    },
  }
);

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  isLoading?: boolean;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, isLoading, leftIcon, rightIcon, children, disabled, ...props }, ref) => {
    return (
      <button
        className={cn(buttonVariants({ variant, size, className }))}
        ref={ref}
        disabled={disabled || isLoading}
        {...props}
      >
        {isLoading ? (
          <Loader2 className="w-4 h-4 animate-spin text-current" />
        ) : (
          leftIcon
        )}
        {children}
        {!isLoading && rightIcon}
      </button>
    );
  }
);

Button.displayName = 'Button';
