import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { CheckCircle2, AlertTriangle, AlertCircle, Info, X } from 'lucide-react';
import { useUI } from '@/contexts/UIContext';
import { cn } from '@/utils/cn';

export const ToastContainer: React.FC = () => {
  const { toasts, removeToast } = useUI();

  const iconMap = {
    success: <CheckCircle2 className="w-4 h-4 text-[#15803D]" />,
    warning: <AlertTriangle className="w-4 h-4 text-[#B45309]" />,
    error: <AlertCircle className="w-4 h-4 text-[#B91C1C]" />,
    info: <Info className="w-4 h-4 text-[#2563EB]" />,
  };

  return (
    <div className="fixed bottom-5 right-5 z-50 flex flex-col space-y-2 max-w-sm w-full pointer-events-none">
      <AnimatePresence>
        {toasts.map((toast) => (
          <motion.div
            key={toast.id}
            initial={{ opacity: 0, y: 15, scale: 0.98 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 8, scale: 0.98 }}
            transition={{ duration: 0.15 }}
            className={cn(
              'pointer-events-auto flex items-start p-3.5 rounded-2xl bg-white dark:bg-[#1B1E23] border border-[#E5E7EB] dark:border-[#2F3540] shadow-lg gap-3'
            )}
          >
            <div className="shrink-0 mt-0.5">{iconMap[toast.type]}</div>
            <div className="flex-1 min-w-0">
              <h5 className="text-xs font-semibold text-[#1F2937] dark:text-[#F3F4F6]">{toast.title}</h5>
              {toast.message && <p className="text-[11px] text-[#6B7280] dark:text-[#9CA3AF] mt-0.5 leading-relaxed">{toast.message}</p>}
            </div>
            <button
              onClick={() => removeToast(toast.id)}
              className="shrink-0 text-[#9CA3AF] hover:text-[#1F2937] dark:hover:text-[#F3F4F6] p-0.5 rounded transition-colors"
              aria-label="Dismiss notification"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          </motion.div>
        ))}
      </AnimatePresence>
    </div>
  );
};
