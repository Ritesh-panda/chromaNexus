import React, { useState } from 'react';
import { useUI } from '@/contexts/UIContext';
import { Search as SearchIcon, FileText, Activity, GitCommit, Bot, X } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { MOCK_REPORTS, MOCK_TIMELINE_EVENTS, MOCK_DISEASES } from '@/constants/mockData';
import { motion, AnimatePresence } from 'framer-motion';

export const GlobalSearchModal: React.FC = () => {
  const { searchOpen, setSearchOpen } = useUI();
  const [query, setQuery] = useState('');
  const navigate = useNavigate();

  if (!searchOpen) return null;

  const filteredReports = MOCK_REPORTS.filter(
    (r) =>
      r.title.toLowerCase().includes(query.toLowerCase()) ||
      r.hospitalName.toLowerCase().includes(query.toLowerCase())
  );
  const filteredEvents = MOCK_TIMELINE_EVENTS.filter(
    (e) =>
      e.title.toLowerCase().includes(query.toLowerCase()) ||
      e.description.toLowerCase().includes(query.toLowerCase())
  );
  const filteredDiseases = MOCK_DISEASES.filter((d) =>
    d.name.toLowerCase().includes(query.toLowerCase())
  );

  const handleSelect = (path: string) => {
    setSearchOpen(false);
    navigate(path);
  };

  return (
    <AnimatePresence>
      <div className="fixed inset-0 z-50 flex items-start justify-center pt-16 sm:pt-24 p-4">
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          onClick={() => setSearchOpen(false)}
          className="fixed inset-0 bg-[#1F2937]/35 backdrop-blur-sm"
        />

        <motion.div
          initial={{ opacity: 0, scale: 0.97, y: -8 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.97, y: -8 }}
          transition={{ duration: 0.16 }}
          className="relative w-full max-w-2xl bg-white dark:bg-[#1B1E23] border border-[#E5E7EB] dark:border-[#2F3540] rounded-2xl shadow-2xl overflow-hidden z-10 p-0"
        >
          {/* Search Header */}
          <div className="flex items-center px-4 py-3.5 border-b border-[#E5E7EB] dark:border-[#2F3540]">
            <SearchIcon className="w-4 h-4 text-[#10B981] mr-3 shrink-0" />
            <input
              type="text"
              autoFocus
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search across reports, diagnoses, medications, and timeline..."
              className="w-full bg-transparent text-[#1F2937] dark:text-[#F3F4F6] placeholder:text-[#9CA3AF] focus:outline-none text-sm font-medium"
            />
            <button
              onClick={() => setSearchOpen(false)}
              className="p-1 rounded-lg text-[#9CA3AF] hover:text-[#1F2937] dark:hover:text-[#F3F4F6] hover:bg-[#F3F1ED] dark:hover:bg-[#23272E]"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          <div className="max-h-96 overflow-y-auto p-4 space-y-4">
            {/* Quick Actions */}
            <div>
              <span className="text-[10px] font-semibold uppercase tracking-wider text-[#9CA3AF]">Quick Navigation</span>
              <div className="grid grid-cols-2 gap-2 mt-2">
                <button
                  onClick={() => handleSelect('/vault')}
                  className="flex items-center gap-2 p-2.5 rounded-xl bg-[#FAF8F5] dark:bg-[#23272E] hover:bg-[#F3F1ED] dark:hover:bg-[#2D323B] border border-[#E5E7EB] dark:border-[#2F3540] text-xs font-medium text-[#1F2937] dark:text-[#F3F4F6] transition-colors text-left"
                >
                  <FileText className="w-3.5 h-3.5 text-[#10B981]" />
                  <span>Medical Vault</span>
                </button>
                <button
                  onClick={() => handleSelect('/chat')}
                  className="flex items-center gap-2 p-2.5 rounded-xl bg-[#FAF8F5] dark:bg-[#23272E] hover:bg-[#F3F1ED] dark:hover:bg-[#2D323B] border border-[#E5E7EB] dark:border-[#2F3540] text-xs font-medium text-[#1F2937] dark:text-[#F3F4F6] transition-colors text-left"
                >
                  <Bot className="w-3.5 h-3.5 text-[#10B981]" />
                  <span>Ask AI Assistant</span>
                </button>
              </div>
            </div>

            {/* Results */}
            {query && (
              <>
                {filteredDiseases.length > 0 && (
                  <div>
                    <span className="text-[10px] font-semibold uppercase tracking-wider text-[#9CA3AF]">Diagnoses & Conditions</span>
                    <div className="space-y-1 mt-1.5">
                      {filteredDiseases.map((d) => (
                        <div
                          key={d.id}
                          onClick={() => handleSelect('/dashboard')}
                          className="flex items-center justify-between p-2.5 rounded-xl hover:bg-[#FAF8F5] dark:hover:bg-[#23272E] border border-transparent hover:border-[#E5E7EB] dark:hover:border-[#2F3540] cursor-pointer text-xs"
                        >
                          <div className="flex items-center space-x-2">
                            <Activity className="w-3.5 h-3.5 text-[#B91C1C]" />
                            <span className="font-semibold text-[#1F2937] dark:text-[#F3F4F6]">{d.name}</span>
                          </div>
                          <span className="text-[#6B7280] dark:text-[#9CA3AF] capitalize">{d.status}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {filteredReports.length > 0 && (
                  <div>
                    <span className="text-[10px] font-semibold uppercase tracking-wider text-[#9CA3AF]">Medical Reports</span>
                    <div className="space-y-1 mt-1.5">
                      {filteredReports.map((r) => (
                        <div
                          key={r.id}
                          onClick={() => handleSelect('/reports')}
                          className="flex items-center justify-between p-2.5 rounded-xl hover:bg-[#FAF8F5] dark:hover:bg-[#23272E] border border-transparent hover:border-[#E5E7EB] dark:hover:border-[#2F3540] cursor-pointer text-xs"
                        >
                          <div className="flex items-center space-x-2">
                            <FileText className="w-3.5 h-3.5 text-[#10B981]" />
                            <span className="font-semibold text-[#1F2937] dark:text-[#F3F4F6]">{r.title}</span>
                          </div>
                          <span className="text-[#6B7280] dark:text-[#9CA3AF] font-mono tabular-nums">{r.reportDate}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {filteredEvents.length > 0 && (
                  <div>
                    <span className="text-[10px] font-semibold uppercase tracking-wider text-[#9CA3AF]">Timeline Events</span>
                    <div className="space-y-1 mt-1.5">
                      {filteredEvents.map((e) => (
                        <div
                          key={e.id}
                          onClick={() => handleSelect('/timeline')}
                          className="flex items-center justify-between p-2.5 rounded-xl hover:bg-[#FAF8F5] dark:hover:bg-[#23272E] border border-transparent hover:border-[#E5E7EB] dark:hover:border-[#2F3540] cursor-pointer text-xs"
                        >
                          <div className="flex items-center space-x-2">
                            <GitCommit className="w-3.5 h-3.5 text-[#4B5563]" />
                            <span className="font-semibold text-[#1F2937] dark:text-[#F3F4F6]">{e.title}</span>
                          </div>
                          <span className="text-[#6B7280] dark:text-[#9CA3AF] font-mono tabular-nums">{e.date}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </>
            )}
          </div>
        </motion.div>
      </div>
    </AnimatePresence>
  );
};
