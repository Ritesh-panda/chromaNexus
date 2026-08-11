import React from 'react';
import type { ChatMessage } from '../../types';
import { Avatar } from '../ui/Avatar';
import { Badge } from '../ui/Badge';
import { Sparkles, FileText, CheckCircle } from 'lucide-react';
import { motion } from 'framer-motion';

export interface ChatBubbleProps {
  message: ChatMessage;
  onCitationClick?: (reportId: string) => void;
}

export const ChatBubble: React.FC<ChatBubbleProps> = ({ message, onCitationClick }) => {
  const isAi = message.sender === 'ai';

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.2 }}
      className={`flex items-start space-x-3 ${isAi ? '' : 'flex-row-reverse space-x-reverse'}`}
    >
      {isAi ? (
        <div className="w-9 h-9 rounded-2xl bg-gradient-to-tr from-blue-600 to-emerald-500 text-white flex items-center justify-center shadow-md shadow-blue-500/20 shrink-0">
          <Sparkles className="w-4 h-4" />
        </div>
      ) : (
        <Avatar size="sm" name="Alex Vance" />
      )}

      <div className={`flex flex-col space-y-1.5 max-w-2xl ${isAi ? 'items-start' : 'items-end'}`}>
        <div className="flex items-center space-x-2 px-1">
          <span className="text-[11px] font-semibold text-slate-500 dark:text-slate-400">
            {isAi ? 'ChronaNexus AI' : 'Alex Vance'}
          </span>
          <span className="text-[10px] text-slate-400">{message.timestamp}</span>
          {isAi && message.reasoningType && (
            <Badge variant={message.reasoningType === 'fact' ? 'success' : 'default'} className="text-[10px] py-0 px-2">
              <CheckCircle className="w-3 h-3 mr-1" /> {message.reasoningType === 'fact' ? 'Verified Fact' : 'Inference'}
            </Badge>
          )}
        </div>

        <div
          className={`p-4 rounded-2xl text-sm leading-relaxed ${
            isAi
              ? 'glass-card border-slate-200 dark:border-slate-800 text-slate-800 dark:text-slate-100 rounded-tl-sm'
              : 'bg-blue-600 text-white rounded-tr-sm shadow-md shadow-blue-600/20'
          }`}
        >
          <div className="whitespace-pre-wrap">{message.text}</div>

          {isAi && message.citations && message.citations.length > 0 && (
            <div className="mt-3 pt-3 border-t border-slate-200/80 dark:border-slate-800/80 space-y-2">
              <span className="text-[11px] font-semibold tracking-wider uppercase text-slate-400 flex items-center gap-1">
                <FileText className="w-3 h-3" /> Grounded Citations ({message.citations.length})
              </span>
              <div className="flex flex-wrap gap-2">
                {message.citations.map((citation, idx) => (
                  <button
                    key={idx}
                    onClick={() => onCitationClick && onCitationClick(citation.reportId)}
                    className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-xl bg-blue-50 dark:bg-blue-950/60 hover:bg-blue-100 dark:hover:bg-blue-900/60 text-blue-700 dark:text-blue-300 text-xs font-medium border border-blue-200 dark:border-blue-800/50 transition-colors"
                  >
                    <span>📄</span>
                    <span className="font-semibold">{citation.reportTitle}</span>
                    <span className="opacity-75">({citation.date})</span>
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
