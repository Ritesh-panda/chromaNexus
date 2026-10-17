import React, { useState } from 'react';
import { Eye, EyeOff } from 'lucide-react';
import { cn } from '@/utils/cn';

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
}

export const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ className, type = 'text', label, error, leftIcon, rightIcon, id, ...props }, ref) => {
    const [showPassword, setShowPassword] = useState(false);
    const inputId = id || (label ? label.toLowerCase().replace(/\s+/g, '-') : undefined);
    const isPassword = type === 'password';
    const effectiveType = isPassword ? (showPassword ? 'text' : 'password') : type;

    return (
      <div className="w-full flex flex-col space-y-1.5">
        {label && (
          <label htmlFor={inputId} className="text-xs font-medium text-[#4B5563] dark:text-[#9CA3AF]">
            {label}
          </label>
        )}
        <div className="relative flex items-center">
          {leftIcon && (
            <div className="absolute left-3.5 text-[#9CA3AF] pointer-events-none flex items-center">
              {leftIcon}
            </div>
          )}
          <input
            id={inputId}
            type={effectiveType}
            className={cn(
              'w-full h-10 rounded-xl bg-white dark:bg-[#1B1E23] border border-[#E5E7EB] dark:border-[#2F3540] px-3.5 text-sm text-[#1F2937] dark:text-[#F3F4F6] placeholder:text-[#9CA3AF] focus:outline-none focus:ring-2 focus:ring-emerald-500/15 focus:border-[#10B981] transition-all duration-150',
              leftIcon && 'pl-10',
              (rightIcon || isPassword) && 'pr-10',
              error && 'border-[#B91C1C] focus:ring-rose-500/15 focus:border-[#B91C1C]',
              className
            )}
            ref={ref}
            {...props}
          />
          {rightIcon ? (
            <div className="absolute right-3 text-[#9CA3AF] flex items-center">
              {rightIcon}
            </div>
          ) : isPassword ? (
            <button
              type="button"
              onClick={() => setShowPassword((prev) => !prev)}
              aria-label={showPassword ? 'Hide password' : 'Show password'}
              tabIndex={-1}
              className="absolute right-3 p-1 rounded-lg text-[#9CA3AF] hover:text-[#1F2937] dark:hover:text-[#F3F4F6] transition-colors focus:outline-none"
            >
              {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
            </button>
          ) : null}
        </div>
        {error && <p className="text-xs text-[#B91C1C] font-medium mt-0.5">{error}</p>}
      </div>
    );
  }
);

Input.displayName = 'Input';

