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
        <SearchIcon className="absolute left-3.5 w-4 h-4 text-slate-400 pointer-events-none" />
        <input
          ref={ref}
          type="text"
          value={value}
          onChange={onChange}
          placeholder={placeholder}
          className={cn(
            'w-full h-10 pl-10 pr-10 rounded-2xl bg-slate-100/80 dark:bg-slate-800/60 border border-transparent focus:border-blue-500/50 dark:focus:border-blue-500/50 text-sm text-slate-900 dark:text-slate-100 placeholder:text-slate-400 focus:outline-none focus:bg-white dark:focus:bg-[#0B0F19] transition-all duration-200',
            className
          )}
          {...props}
        />
        {value && (
          <button
            type="button"
            onClick={onClear}
            className="absolute right-3.5 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        )}
      </div>
    );
  }
);

Search.displayName = 'Search';
