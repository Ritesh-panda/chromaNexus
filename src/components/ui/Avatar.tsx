import React from 'react';
import { cn } from '@/utils/cn';

export interface AvatarProps extends React.HTMLAttributes<HTMLDivElement> {
  src?: string;
  name?: string;
  size?: 'sm' | 'md' | 'lg' | 'xl';
}

export const Avatar: React.FC<AvatarProps> = ({ src, name, size = 'md', className, ...props }) => {
  const sizeClasses = {
    sm: 'w-7 h-7 text-xs',
    md: 'w-9 h-9 text-xs font-medium',
    lg: 'w-11 h-11 text-sm font-semibold',
    xl: 'w-16 h-16 text-lg font-semibold',
  };

  const getInitials = (n?: string) => {
    if (!n) return 'CN';
    const parts = n.trim().split(' ');
    if (parts.length >= 2) return `${parts[0][0]}${parts[1][0]}`.toUpperCase();
    return n.slice(0, 2).toUpperCase();
  };

  return (
    <div
      className={cn(
        'relative inline-flex items-center justify-center rounded-full bg-[#F3F1ED] dark:bg-[#2F3540] text-[#1F2937] dark:text-[#F3F4F6] font-medium overflow-hidden shrink-0 border border-[#E5E7EB] dark:border-[#2F3540]',
        sizeClasses[size],
        className
      )}
      {...props}
    >
      {src ? (
        <img src={src} alt={name || 'Avatar'} className="w-full h-full object-cover" />
      ) : (
        <span>{getInitials(name)}</span>
      )}
    </div>
  );
};
