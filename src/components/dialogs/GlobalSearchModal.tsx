import React, { useState } from 'react';
import { useUI } from '../../contexts/UIContext';
import { Search as SearchIcon, FileText, Activity, GitCommit, Bot, X } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { MOCK_REPORTS, MOCK_TIMELINE_EVENTS, MOCK_DISEASES } from '../../constants/mockData';
import { motion, AnimatePresence } from 'framer-motion';

export const GlobalSearchModal: React.FC = () => {
  const { searchOpen, setSearchOpen } = useUI();
  const [query, setQuery] = useState('');
  const navigate = useNavigate();

  if (!searchOpen) return null;

  const filteredReports = MOCK_REPORTS.filter(r => r.title.toLowerCase().includes(query.toLowerCase()) || r.hospitalName.toLowerCase().includes(query.toLowerCase()));
  const filteredEvents = MOCK_TIMELINE_EVENTS.filter(e => e.title.toLowerCase().includes(query.toLowerCase()) || e.description.toLowerCase().includes(query.toLowerCase()));
  const filteredDiseases = MOCK_DISEASES.filter(d => d.name.toLowerCase().includes(query.toLowerCase()));

  const handleSelect = (path: string) => {
    setSearchOpen(false);
    navigate(path);
  };

  return (
    <AnimatePresence>
      <div className="fixed inset-0 z-50 flex items-start justify-center pt-20 p-4">
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          onClick={() => setSearchOpen(false)}
          className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm"
        />

        <motion.div
          initial={{ opacity: 0, scale: 0.95, y: -10 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.95, y: -10 }}
          className="relative w-full max-w-2xl glass-card border border-slate-200 dark:border-slate-800 shadow-2xl overflow-hidden z-10 p-0"
        >
          <div className="flex items-center px-4 py-3.5 border-b border-slate-200 dark:border-slate-800">
            <SearchIcon className="w-5 h-5 text-blue-500 mr-3" />
            <input
              type="text"
              autoFocus
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search across reports, diagnoses, medications, and timeline..."
              className="w-full bg-transparent text-slate-900 dark:text-slate-100 placeholder:text-slate-400 focus:outline-none text-base font-medium"
            />
            <button onClick={() => setSearchOpen(false)} className="p-1 rounded-lg text-slate-400 hover:text-slate-600 dark:hover:text-slate-200">
              <X className="w-5 h-5" />
            </button>
          </div>

          <div className="max-h-96 overflow-y-auto p-4 space-y-4">
            {/* Quick Actions */}
            <div>
              <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400">Quick Navigation</span>
              <div className="grid grid-cols-2 gap-2 mt-2">
                <button
                  onClick={() => handleSelect('/vault')}
                  className="flex items-center gap-2 p-2.5 rounded-xl bg-slate-100/70 dark:bg-slate-800/60 hover:bg-blue-50 dark:hover:bg-blue-950/60 text-xs font-semibold text-slate-700 dark:text-slate-300 transition-colors text-left"
                >
                  <FileText className="w-4 h-4 text-blue-500" />
                  <span>Medical Vault</span>
                </button>
                <button
                  onClick={() => handleSelect('/chat')}
                  className="flex items-center gap-2 p-2.5 rounded-xl bg-slate-100/70 dark:bg-slate-800/60 hover:bg-blue-50 dark:hover:bg-blue-950/60 text-xs font-semibold text-slate-700 dark:text-slate-300 transition-colors text-left"
                >
                  <Bot className="w-4 h-4 text-emerald-500" />
                  <span>Ask AI Assistant</span>
                </button>
              </div>
            </div>

            {/* Results */}
            {query && (
              <>
                {filteredDiseases.length > 0 && (
                  <div>
                    <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400">Diagnoses & Conditions</span>
                    <div className="space-y-1 mt-1">
                      {filteredDiseases.map((d) => (
                        <div
                          key={d.id}
                          onClick={() => handleSelect('/dashboard')}
                          className="flex items-center justify-between p-2.5 rounded-xl hover:bg-slate-100 dark:hover:bg-slate-800/80 cursor-pointer text-xs"
                        >
                          <span className="font-semibold text-slate-800 dark:text-slate-200 flex items-center gap-2">
                            <Activity className="w-3.5 h-3.5 text-rose-500" /> {d.name}
                          </span>
                          <span className="text-[10px] text-slate-400">Diagnosed: {d.diagnosedDate}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {filteredReports.length > 0 && (
                  <div>
                    <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400">Medical Reports</span>
                    <div className="space-y-1 mt-1">
                      {filteredReports.map((r) => (
                        <div
                          key={r.id}
                          onClick={() => handleSelect('/reports')}
                          className="flex items-center justify-between p-2.5 rounded-xl hover:bg-slate-100 dark:hover:bg-slate-800/80 cursor-pointer text-xs"
                        >
                          <span className="font-semibold text-slate-800 dark:text-slate-200 flex items-center gap-2">
                            <FileText className="w-3.5 h-3.5 text-blue-500" /> {r.title}
                          </span>
                          <span className="text-[10px] text-slate-400">{r.hospitalName}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {filteredEvents.length > 0 && (
                  <div>
                    <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400">Timeline Milestones</span>
                    <div className="space-y-1 mt-1">
                      {filteredEvents.map((e) => (
                        <div
                          key={e.id}
                          onClick={() => handleSelect('/timeline')}
                          className="flex items-center justify-between p-2.5 rounded-xl hover:bg-slate-100 dark:hover:bg-slate-800/80 cursor-pointer text-xs"
                        >
                          <span className="font-semibold text-slate-800 dark:text-slate-200 flex items-center gap-2">
                            <GitCommit className="w-3.5 h-3.5 text-purple-500" /> {e.title}
                          </span>
                          <span className="text-[10px] text-slate-400">{e.date}</span>
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
