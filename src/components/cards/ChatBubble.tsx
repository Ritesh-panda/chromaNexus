import React, { useState } from 'react';
import type { ChatMessage } from '@/types';
import { Avatar } from '@/components/ui/Avatar';
import { Badge } from '@/components/ui/Badge';
import { 
  FileText, 
  ShieldCheck, 
  AlertTriangle, 
  PhoneCall, 
  Sparkles, 
  Volume2, 
  VolumeX, 
  Building2 
} from 'lucide-react';
import { ClinicalTrendCard } from '@/components/cards/ClinicalTrendCard';
import { motion } from 'framer-motion';
import { useAuth } from '@/contexts/AuthContext';

export interface ChatBubbleProps {
  message: ChatMessage;
  onCitationClick?: (reportId: string) => void;
  onPromptClick?: (prompt: string) => void;
  onFindHospitals?: () => void;
}

export const ChatBubble: React.FC<ChatBubbleProps> = ({ 
  message, 
  onCitationClick, 
  onPromptClick,
  onFindHospitals 
}) => {
  const { user } = useAuth();
  const [isSpeaking, setIsSpeaking] = useState(false);
  const isAi = message.sender === 'ai';
  const userName = user?.name || 'Patient';

  const handleToggleSpeak = () => {
    if (!('speechSynthesis' in window)) return;
    if (isSpeaking) {
      window.speechSynthesis.cancel();
      setIsSpeaking(false);
      return;
    }

    window.speechSynthesis.cancel();
    // Clean markdown for natural human-like voice synthesis
    const clean = message.text
      .replace(/[#*_`~]/g, '')
      .replace(/\[([^\]]+)\]\([^)]+\)/g, '$1')
      .replace(/•/g, '')
      .replace(/\n+/g, ' ');

    const utterance = new SpeechSynthesisUtterance(clean);

    // Auto-detect utterance language from character script
    if (/[\u0B00-\u0B7F]/.test(clean)) {
      utterance.lang = 'or-IN';
    } else if (/[\u0900-\u097F]/.test(clean)) {
      utterance.lang = 'hi-IN';
    } else if (/[\u0C00-\u0C7F]/.test(clean)) {
      utterance.lang = 'te-IN';
    } else if (/[\u0B80-\u0BFF]/.test(clean)) {
      utterance.lang = 'ta-IN';
    } else if (/[\u0980-\u09FF]/.test(clean)) {
      utterance.lang = 'bn-IN';
    } else {
      utterance.lang = 'en-IN';
    }

    const voices = window.speechSynthesis.getVoices();
    const matchedVoice = voices.find((v) => 
      v.lang.toLowerCase() === utterance.lang.toLowerCase() ||
      v.lang.toLowerCase().startsWith(utterance.lang.slice(0, 2))
    );
    if (matchedVoice) {
      utterance.voice = matchedVoice;
    }

    utterance.rate = 0.95;
    utterance.onend = () => setIsSpeaking(false);
    utterance.onerror = () => setIsSpeaking(false);
    window.speechSynthesis.speak(utterance);
    setIsSpeaking(true);
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.15 }}
      className={`flex items-start space-x-3 ${isAi ? '' : 'flex-row-reverse space-x-reverse'}`}
    >
      {isAi ? (
        <div className={`w-8 h-8 rounded-xl ${message.isEmergency ? 'bg-red-100 text-red-600 dark:bg-red-950/60 dark:text-red-400 border border-red-300 dark:border-red-800' : 'bg-[#ECFDF5] dark:bg-emerald-950/40 border border-emerald-200/60 dark:border-emerald-800/40 text-[#10B981]'} flex items-center justify-center font-semibold text-xs shrink-0`}>
          {message.isEmergency ? '🚨' : 'CN'}
        </div>
      ) : (
        <Avatar size="sm" name={userName} />
      )}

      <div className={`flex flex-col space-y-1.5 max-w-2xl ${isAi ? 'items-start' : 'items-end'}`}>
        <div className="flex items-center space-x-2 px-1">
          <span className="text-[11px] font-medium text-[#6B7280] dark:text-[#9CA3AF]">
            {isAi ? 'ChronaNexus Clinical Assistant' : userName}
          </span>
          <span className="text-[10px] text-[#9CA3AF] tabular-nums">{message.timestamp}</span>

          {isAi && (
            <button
              onClick={handleToggleSpeak}
              className={`p-1 rounded-md transition-colors ${
                isSpeaking 
                  ? 'text-emerald-600 bg-emerald-100 dark:bg-emerald-950/60 dark:text-emerald-400' 
                  : 'text-[#9CA3AF] hover:text-[#4B5563] dark:hover:text-[#D1D5DB]'
              }`}
              title={isSpeaking ? 'Stop reading' : 'Read response aloud (Voice)'}
            >
              {isSpeaking ? <VolumeX className="w-3.5 h-3.5" /> : <Volume2 className="w-3.5 h-3.5" />}
            </button>
          )}

          {isAi && message.isEmergency && (
            <Badge variant="danger" className="text-[10px] py-0 px-2 font-bold animate-pulse">
              Emergency Protocol (108)
            </Badge>
          )}
          {isAi && !message.isEmergency && message.reasoningType && (
            <Badge variant={message.reasoningType === 'fact' ? 'success' : 'default'} className="text-[10px] py-0 px-2 font-normal">
              <ShieldCheck className="w-3 h-3 mr-1" /> {message.reasoningType === 'fact' ? 'Verified Extraction' : 'Inference'}
            </Badge>
          )}
        </div>

        <div
          className={`p-4 rounded-2xl text-xs sm:text-sm leading-relaxed ${
            isAi
              ? message.isEmergency
                ? 'bg-red-50/50 dark:bg-red-950/20 border border-red-300/80 dark:border-red-800/60 text-[#1F2937] dark:text-[#F3F4F6] rounded-tl-sm shadow-sm'
                : 'bg-white dark:bg-[#1B1E23] border border-[#E5E7EB] dark:border-[#2F3540] text-[#1F2937] dark:text-[#F3F4F6] rounded-tl-sm shadow-[0_1px_2px_0_rgba(0,0,0,0.02)]'
              : 'bg-[#1F2937] text-white dark:bg-[#10B981] dark:text-white rounded-tr-sm shadow-sm'
          }`}
        >
          {/* Emergency Alert Banner */}
          {isAi && message.isEmergency && (
            <div className="mb-3.5 p-3.5 rounded-xl bg-red-500/10 border border-red-500/30 flex items-start gap-3 text-red-600 dark:text-red-400">
              <AlertTriangle className="w-5 h-5 shrink-0 text-red-500 mt-0.5" />
              <div className="space-y-1.5 flex-1">
                <div className="font-semibold text-xs tracking-wider uppercase text-red-600 dark:text-red-400 flex items-center justify-between">
                  <span>Critical Emergency Action Required</span>
                  <span className="text-[10px] px-2 py-0.5 rounded-full bg-red-600 text-white font-bold animate-pulse">108 / 112</span>
                </div>
                <p className="text-xs text-red-700 dark:text-red-300 leading-snug">
                  Potentially life-threatening symptoms detected. Please contact emergency services or proceed to the nearest emergency room immediately.
                </p>
                <div className="pt-1 flex flex-wrap gap-2">
                  <a
                    href="tel:108"
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-red-600 text-white font-semibold text-xs hover:bg-red-700 transition shadow-sm"
                  >
                    <PhoneCall className="w-3.5 h-3.5" /> Call 108 (Ambulance)
                  </a>
                  <a
                    href="tel:112"
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-neutral-900 dark:bg-white text-white dark:text-neutral-900 font-semibold text-xs hover:opacity-90 transition shadow-sm"
                  >
                    <PhoneCall className="w-3.5 h-3.5" /> Call 112
                  </a>
                  <button
                    onClick={() => onFindHospitals && onFindHospitals()}
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-white dark:bg-[#1B1E23] text-red-700 dark:text-red-300 border border-red-300 dark:border-red-800 font-semibold text-xs hover:bg-red-50 dark:hover:bg-red-950/40 transition shadow-sm"
                  >
                    <Building2 className="w-3.5 h-3.5 text-red-500" /> Nearby Hospitals (OSM)
                  </button>
                </div>
              </div>
            </div>
          )}

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

          {/* Dynamic Context-Aware Follow-Up Chips */}
          {isAi && message.followUpSuggestions && message.followUpSuggestions.length > 0 && (
            <div className="mt-3.5 pt-3 border-t border-[#E5E7EB]/80 dark:border-[#2F3540] space-y-1.5">
              <span className="text-[10px] font-semibold text-[#6B7280] dark:text-[#9CA3AF] flex items-center gap-1">
                <Sparkles className="w-3 h-3 text-emerald-500" /> Suggested Follow-Ups:
              </span>
              <div className="flex flex-wrap gap-1.5">
                {message.followUpSuggestions.map((suggestion, sIdx) => (
                  <button
                    key={sIdx}
                    onClick={() => onPromptClick && onPromptClick(suggestion)}
                    className="text-left text-xs px-2.5 py-1 rounded-lg bg-[#F0FDF4] dark:bg-emerald-950/40 text-emerald-800 dark:text-emerald-300 border border-emerald-200/80 dark:border-emerald-800/50 hover:bg-emerald-100 dark:hover:bg-emerald-900/50 transition-colors font-medium flex items-center gap-1"
                  >
                    <span>→</span>
                    <span>{suggestion}</span>
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
