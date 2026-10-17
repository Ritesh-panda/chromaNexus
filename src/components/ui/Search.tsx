import React from 'react';
import { Search as SearchIcon, X } from 'lucide-react';
import { cn } from '@/utils/cn';

export interface SearchProps extends React.InputHTMLAttributes<HTMLInputElement> {
  onClear?: () => void;
}

export const Search = React.forwardRef<HTMLInputElement, SearchProps>(
  ({ className, value, onChange, onClear, placeholder = 'Search medical history, reports, diagnoses...', ...props }, ref) => {
    return (
      <div className="relative w-full flex items-center">
        <SearchIcon className="absolute left-3.5 w-4 h-4 text-[#9CA3AF] pointer-events-none" />
        <input
          ref={ref}
          type="text"
          value={value}
          onChange={onChange}
          placeholder={placeholder}
          className={cn(
            'w-full h-10 pl-10 pr-10 rounded-xl bg-[#F3F1ED] dark:bg-[#23272E] border border-transparent focus:border-[#10B981] focus:bg-white dark:focus:bg-[#1B1E23] text-sm text-[#1F2937] dark:text-[#F3F4F6] placeholder:text-[#9CA3AF] focus:outline-none focus:ring-2 focus:ring-emerald-500/15 transition-all duration-150',
            className
          )}
          {...props}
        />
        {value && (
          <button
            type="button"
            onClick={onClear}
            className="absolute right-3.5 text-[#9CA3AF] hover:text-[#1F2937] dark:hover:text-[#F3F4F6] transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        )}
      </div>
    );
  }
);

Search.displayName = 'Search';
