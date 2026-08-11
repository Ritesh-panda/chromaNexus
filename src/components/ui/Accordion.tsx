import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ChevronDown } from 'lucide-react';
import { cn } from '../../utils/cn';

export interface AccordionItem {
  id: string;
  title: string;
  subtitle?: string;
  icon?: React.ReactNode;
  content: React.ReactNode;
}

export interface AccordionProps {
  items: AccordionItem[];
  allowMultiple?: boolean;
  className?: string;
}

export const Accordion: React.FC<AccordionProps> = ({ items, allowMultiple = false, className }) => {
  const [openIds, setOpenIds] = useState<string[]>([items[0]?.id || '']);

  const toggleItem = (id: string) => {
    if (allowMultiple) {
      setOpenIds((prev) => (prev.includes(id) ? prev.filter((i) => i !== id) : [...prev, id]));
    } else {
      setOpenIds((prev) => (prev.includes(id) ? [] : [id]));
    }
  };

  return (
    <div className={cn('space-y-3', className)}>
      {items.map((item) => {
        const isOpen = openIds.includes(item.id);
        return (
          <div
            key={item.id}
            className="glass-card border border-slate-200 dark:border-slate-800/80 rounded-2xl overflow-hidden"
          >
            <button
              type="button"
              onClick={() => toggleItem(item.id)}
              className="w-full flex items-center justify-between p-4 text-left transition-colors hover:bg-slate-50/50 dark:hover:bg-slate-800/40"
            >
              <div className="flex items-center space-x-3">
                {item.icon && <div className="text-blue-600 dark:text-blue-400">{item.icon}</div>}
                <div>
                  <h4 className="text-sm font-semibold text-slate-900 dark:text-slate-100">{item.title}</h4>
                  {item.subtitle && <p className="text-xs text-slate-500 dark:text-slate-400">{item.subtitle}</p>}
                </div>
              </div>
              <ChevronDown
                className={cn('w-4 h-4 text-slate-400 transition-transform duration-200', isOpen && 'rotate-180')}
              />
            </button>
            <AnimatePresence initial={false}>
              {isOpen && (
                <motion.div
                  initial={{ height: 0, opacity: 0 }}
                  animate={{ height: 'auto', opacity: 1 }}
                  exit={{ height: 0, opacity: 0 }}
                  transition={{ duration: 0.2 }}
                >
                  <div className="p-4 pt-0 text-sm text-slate-600 dark:text-slate-300 border-t border-slate-100 dark:border-slate-800/60">
                    {item.content}
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        );
      })}
    </div>
  );
};
