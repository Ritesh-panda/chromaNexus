import React from 'react';
import type { ChatMessage } from '@/types';
import { Avatar } from '@/components/ui/Avatar';
import { Badge } from '@/components/ui/Badge';
import { FileText, ShieldCheck } from 'lucide-react';
import { ClinicalTrendCard } from '@/components/cards/ClinicalTrendCard';
import { motion } from 'framer-motion';

export interface ChatBubbleProps {
  message: ChatMessage;
  onCitationClick?: (reportId: string) => void;
}

export const ChatBubble: React.FC<ChatBubbleProps> = ({ message, onCitationClick }) => {
  const isAi = message.sender === 'ai';

  return (
    <motion.div
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.15 }}
      className={`flex items-start space-x-3 ${isAi ? '' : 'flex-row-reverse space-x-reverse'}`}
    >
      {isAi ? (
        <div className="w-8 h-8 rounded-xl bg-[#ECFDF5] dark:bg-emerald-950/40 border border-emerald-200/60 dark:border-emerald-800/40 text-[#10B981] flex items-center justify-center font-semibold text-xs shrink-0">
          CN
        </div>
      ) : (
        <Avatar size="sm" name="Alex Vance" />
      )}

      <div className={`flex flex-col space-y-1.5 max-w-2xl ${isAi ? 'items-start' : 'items-end'}`}>
        <div className="flex items-center space-x-2 px-1">
          <span className="text-[11px] font-medium text-[#6B7280] dark:text-[#9CA3AF]">
            {isAi ? 'ChronaNexus Clinical Assistant' : 'Alex Vance'}
          </span>
          <span className="text-[10px] text-[#9CA3AF] tabular-nums">{message.timestamp}</span>
          {isAi && message.reasoningType && (
            <Badge variant={message.reasoningType === 'fact' ? 'success' : 'default'} className="text-[10px] py-0 px-2 font-normal">
              <ShieldCheck className="w-3 h-3 mr-1" /> {message.reasoningType === 'fact' ? 'Verified Extraction' : 'Inference'}
            </Badge>
          )}
        </div>

        <div
          className={`p-4 rounded-2xl text-xs sm:text-sm leading-relaxed ${
            isAi
              ? 'bg-white dark:bg-[#1B1E23] border border-[#E5E7EB] dark:border-[#2F3540] text-[#1F2937] dark:text-[#F3F4F6] rounded-tl-sm shadow-[0_1px_2px_0_rgba(0,0,0,0.02)]'
              : 'bg-[#1F2937] text-white dark:bg-[#10B981] dark:text-white rounded-tr-sm shadow-sm'
          }`}
        >
          <div className="whitespace-pre-wrap">{message.text}</div>

          {isAi && message.structuredTrend && (
            <ClinicalTrendCard trend={message.structuredTrend} onCitationClick={onCitationClick} />
          )}

          {isAi && message.citations && message.citations.length > 0 && (
            <div className="mt-3.5 pt-3 border-t border-[#E5E7EB]/80 dark:border-[#2F3540] space-y-2">
              <span className="text-[10px] font-semibold tracking-wider uppercase text-[#6B7280] dark:text-[#9CA3AF] flex items-center gap-1.5">
                <FileText className="w-3 h-3 text-[#10B981]" /> Grounded Citations ({message.citations.length})
              </span>
              <div className="flex flex-wrap gap-1.5">
                {message.citations.map((citation, idx) => (
                  <button
                    key={idx}
                    onClick={() => onCitationClick && onCitationClick(citation.reportId)}
                    className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-xl bg-[#F3F1ED] hover:bg-[#EBE8E2] dark:bg-[#23272E] dark:hover:bg-[#2D323B] text-[#1F2937] dark:text-[#F3F4F6] text-xs border border-[#E5E7EB] dark:border-[#2F3540] transition-colors"
                  >
                    <span className="opacity-70">📄</span>
                    <span className="font-medium truncate max-w-[200px]">{citation.reportTitle}</span>
                    <span className="text-[#6B7280] dark:text-[#9CA3AF] text-[10px] tabular-nums">({citation.date})</span>
                    {citation.facility && (
                      <span className="text-[10px] text-emerald-600 dark:text-emerald-400 font-medium truncate max-w-[120px]">• {citation.facility}</span>
                    )}
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </motion.div>
  );
};
