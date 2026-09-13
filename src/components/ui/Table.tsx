import React from 'react';
import { cn } from '@/utils/cn';

export interface Column<T> {
  header: string;
  accessor: keyof T | ((row: T) => React.ReactNode);
  className?: string;
}

export interface TableProps<T> {
  columns: Column<T>[];
  data: T[];
  keyExtractor: (row: T) => string;
  onRowClick?: (row: T) => void;
  className?: string;
}

export function Table<T>({ columns, data, keyExtractor, onRowClick, className }: TableProps<T>) {
  return (
    <div className={cn('w-full overflow-x-auto rounded-2xl border border-slate-200 dark:border-slate-800', className)}>
      <table className="w-full text-left text-sm border-collapse">
        <thead className="bg-slate-100/70 dark:bg-slate-800/60 text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
          <tr>
            {columns.map((col, idx) => (
              <th key={idx} className={cn('py-3.5 px-4', col.className)}>
                {col.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100 dark:divide-slate-800/80 bg-white/60 dark:bg-[#131B2E]/60">
          {data.map((row) => (
            <tr
              key={keyExtractor(row)}
              onClick={() => onRowClick && onRowClick(row)}
              className={cn(
                'transition-colors duration-150',
                onRowClick && 'cursor-pointer hover:bg-slate-50/80 dark:hover:bg-slate-800/40'
              )}
            >
              {columns.map((col, idx) => (
                <td key={idx} className={cn('py-3.5 px-4 text-slate-700 dark:text-slate-200', col.className)}>
                  {typeof col.accessor === 'function'
                    ? col.accessor(row)
                    : (row[col.accessor] as unknown as React.ReactNode)}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
