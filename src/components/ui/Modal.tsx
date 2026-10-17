import React, { useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X } from 'lucide-react';
import { cn } from '@/utils/cn';

export interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title?: string;
  description?: string;
  children: React.ReactNode;
  maxWidth?: 'sm' | 'md' | 'lg' | 'xl' | '2xl';
}

export const Modal: React.FC<ModalProps> = ({
  isOpen,
  onClose,
  title,
  description,
  children,
  maxWidth = 'lg',
}) => {
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    if (isOpen) {
      document.body.style.overflow = 'hidden';
      window.addEventListener('keydown', handleKeyDown);
    }
    return () => {
      document.body.style.overflow = 'unset';
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, [isOpen, onClose]);

  const maxWidthClasses = {
    sm: 'max-w-sm',
    md: 'max-w-md',
    lg: 'max-w-lg',
    xl: 'max-w-xl',
    '2xl': 'max-w-2xl',
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 bg-[#1F2937]/35 backdrop-blur-sm"
          />

          <motion.div
            initial={{ opacity: 0, scale: 0.97, y: 8 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.97, y: 8 }}
            transition={{ duration: 0.18, ease: 'easeOut' }}
            className={cn(
              'relative w-full bg-white dark:bg-[#1B1E23] border border-[#E5E7EB] dark:border-[#2F3540] p-6 rounded-2xl shadow-xl z-10 max-h-[90vh] overflow-y-auto',
              maxWidthClasses[maxWidth]
            )}
          >
            <div className="flex items-start justify-between pb-4 mb-4 border-b border-[#E5E7EB] dark:border-[#2F3540]">
              <div>
                {title && <h2 className="text-lg font-semibold text-[#1F2937] dark:text-[#F3F4F6]">{title}</h2>}
                {description && <p className="text-xs text-[#6B7280] dark:text-[#9CA3AF] mt-0.5 leading-relaxed">{description}</p>}
              </div>
              <button
                onClick={onClose}
                className="text-[#9CA3AF] hover:text-[#1F2937] dark:hover:text-[#F3F4F6] p-1.5 rounded-xl hover:bg-[#F3F1ED] dark:hover:bg-[#23272E] transition-colors"
                aria-label="Close dialog"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
            <div>{children}</div>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
};
