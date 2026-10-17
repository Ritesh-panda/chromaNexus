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
    <div className={cn('w-full overflow-x-auto rounded-2xl border border-[#E5E7EB] dark:border-[#2F3540] bg-white dark:bg-[#1B1E23]', className)}>
      <table className="w-full text-left text-sm border-collapse">
        <thead className="bg-[#F3F1ED]/70 dark:bg-[#23272E] text-xs font-medium text-[#6B7280] dark:text-[#9CA3AF]">
          <tr>
            {columns.map((col, idx) => (
              <th key={idx} className={cn('py-3 px-4 font-medium', col.className)}>
                {col.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-[#E5E7EB]/70 dark:divide-[#2F3540] bg-white dark:bg-[#1B1E23]">
          {data.map((row) => (
            <tr
              key={keyExtractor(row)}
              onClick={() => onRowClick && onRowClick(row)}
              className={cn(
                'transition-colors duration-150',
                onRowClick && 'cursor-pointer hover:bg-[#FAF8F5] dark:hover:bg-[#23272E]/50'
              )}
            >
              {columns.map((col, idx) => (
                <td key={idx} className={cn('py-3.5 px-4 text-[#1F2937] dark:text-[#F3F4F6]', col.className)}>
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
