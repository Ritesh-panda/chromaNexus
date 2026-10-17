import React, { useState, useRef, useEffect } from 'react';
import { ChatBubble } from '@/components/cards/ChatBubble';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { useUI } from '@/contexts/UIContext';
import { useUser } from '@/contexts/UserContext';
import type { ChatMessage, ConversationThread } from '@/types';
import { chatService } from '@/services/chat.service';
import {
  MOCK_REPORTS,
  MOCK_DISEASES,
  MOCK_MEDICATIONS,
} from '@/constants/mockData';
import {
  Send,
  Plus,
  MessageSquare,
  ShieldCheck,
  HelpCircle,
  Paperclip,
  Loader2,
  FileQuestion,
  PanelRight,
  Activity,
  Pill,
  FileText,
  UserCheck
} from 'lucide-react';

export const AIChatPage: React.FC = () => {
  const { addToast } = useUI();
  const { patient } = useUser();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [threads, setThreads] = useState<ConversationThread[]>([]);
  const [activeThreadId, setActiveThreadId] = useState<string | null>(null);
  const [inputQuery, setInputQuery] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [isLoadingThreads, setIsLoadingThreads] = useState(true);
  const [isLoadingMessages, setIsLoadingMessages] = useState(false);
  const [showContextPanel, setShowContextPanel] = useState(true);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const suggestedPrompts = [
    'What are the MRI findings and impression for Alex Vance\'s right knee joint?',
    'What is the patient\'s HbA1c level?',
    'What medicines did I take for high blood pressure?',
    'When was my highest cholesterol reading?',
  ];

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    let isMounted = true;
    const loadThreads = async () => {
      setIsLoadingThreads(true);
      try {
        const fetchedThreads = await chatService.getThreads();
        if (isMounted) {
          if (fetchedThreads.length > 0) {
            setThreads(fetchedThreads);
            setActiveThreadId(fetchedThreads[0].id);
          } else {
            const newTh = await chatService.createConversation('New Clinical Inquiry');
            setThreads([newTh]);
            setActiveThreadId(newTh.id);
          }
        }
      } catch {
        if (isMounted) {
          const fallbackThread: ConversationThread = {
            id: `conv_${Date.now()}`,
            title: 'New Clinical Inquiry',
            lastMessageDate: new Date().toISOString(),
            messageCount: 0,
          };
          setThreads([fallbackThread]);
          setActiveThreadId(fallbackThread.id);
        }
      } finally {
        if (isMounted) setIsLoadingThreads(false);
      }
    };
    loadThreads();
    return () => {
      isMounted = false;
    };
  }, []);

  useEffect(() => {
    if (!activeThreadId) return;
    let isMounted = true;
    const loadMessages = async () => {
      setIsLoadingMessages(true);
      try {
        const msgs = await chatService.getMessages(activeThreadId);
        if (isMounted) {
          setMessages(msgs);
        }
      } catch {
        if (isMounted) {
          setMessages([]);
        }
      } finally {
        if (isMounted) setIsLoadingMessages(false);
      }
    };
    loadMessages();
    return () => {
      isMounted = false;
    };
  }, [activeThreadId]);

  useEffect(() => {
    scrollToBottom();
  }, [messages, isTyping]);

  const handleNewConversation = async () => {
    try {
      const newTh = await chatService.createConversation('New Clinical Conversation');
      setThreads((prev) => [newTh, ...prev]);
      setActiveThreadId(newTh.id);
      setMessages([]);
    } catch (err: unknown) {
      const message =
        err && typeof err === 'object' && 'message' in err
          ? String(err.message)
          : 'Could not start new chat session.';
      addToast({
        type: 'error',
        title: 'Conversation Creation Failed',
        message,
      });
    }
  };

  const handleSend = async (textToSend?: string) => {
    const query = textToSend || inputQuery;
    if (!query.trim()) return;

    let targetThreadId = activeThreadId;
    if (!targetThreadId) {
      try {
        const newTh = await chatService.createConversation('New Clinical Inquiry');
        setThreads((prev) => [newTh, ...prev]);
        setActiveThreadId(newTh.id);
        targetThreadId = newTh.id;
      } catch {
        addToast({
          type: 'error',
          title: 'Session Error',
          message: 'Could not create conversation session.',
        });
        return;
      }
    }

    const userMsg: ChatMessage = {
      id: `msg_usr_${Date.now()}`,
      sender: 'user',
      text: query,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInputQuery('');
    setIsTyping(true);

    try {
      const response = await chatService.sendMessage(query, targetThreadId);
      setMessages((prev) => [...prev, response]);
      setThreads((prev) =>
        prev.map((t) => (t.id === targetThreadId ? { ...t, messageCount: t.messageCount + 2 } : t))
      );
    } catch (err: unknown) {
      const message =
        err && typeof err === 'object' && 'message' in err
          ? String(err.message)
          : 'Failed to process clinical query. Please verify backend connection.';
      addToast({
        type: 'error',
        title: 'Assistant Error',
        message,
      });
    } finally {
      setIsTyping(false);
    }
  };

  return (
    <div className="h-[calc(100vh-7.5rem)] flex gap-4 pb-2">
      {/* Left Threads Drawer / Sidebar */}
      <div className="hidden lg:flex w-60 xl:w-64 flex-col bg-white dark:bg-[#1B1E23] rounded-2xl border border-[#E5E7EB] dark:border-[#2F3540] p-3.5 space-y-3.5 shadow-[0_1px_3px_0_rgba(0,0,0,0.02)] shrink-0">
        <Button
          variant="secondary"
          size="sm"
          className="w-full justify-start text-xs font-medium"
          leftIcon={<Plus className="w-4 h-4 text-[#10B981]" />}
          onClick={handleNewConversation}
        >
          New Clinical Inquiry
        </Button>

        <div className="space-y-1 flex-1 overflow-y-auto">
          <span className="text-[10px] font-semibold uppercase tracking-wider text-[#9CA3AF] px-2 block mb-1.5">
            Conversation History
          </span>
          {isLoadingThreads ? (
            <div className="flex items-center justify-center py-6 text-xs text-[#9CA3AF]">
              <Loader2 className="w-3.5 h-3.5 animate-spin mr-2" /> Loading...
            </div>
          ) : threads.length === 0 ? (
            <p className="text-xs text-[#9CA3AF] px-2 py-4 text-center">No conversation history yet.</p>
          ) : (
            threads.map((th) => (
              <button
                key={th.id}
                onClick={() => setActiveThreadId(th.id)}
                className={`w-full flex items-center justify-between p-2.5 rounded-xl text-left text-xs font-medium transition-colors ${
                  activeThreadId === th.id
                    ? 'bg-[#F3F1ED] dark:bg-[#23272E] text-[#1F2937] dark:text-[#F3F4F6] font-semibold border-l-2 border-[#10B981]'
                    : 'text-[#6B7280] dark:text-[#9CA3AF] hover:bg-[#FAF8F5] dark:hover:bg-[#23272E]/60'
                }`}
              >
                <span className="truncate flex items-center gap-2">
                  <MessageSquare className="w-3.5 h-3.5 shrink-0 opacity-70" /> {th.title}
                </span>
                <span className="text-[10px] text-[#9CA3AF] tabular-nums shrink-0">{th.lastMessageDate}</span>
              </button>
            ))
          )}
        </div>

        <div className="p-3 rounded-xl bg-[#FAF8F5] dark:bg-[#23272E]/60 border border-[#E5E7EB] dark:border-[#2F3540] text-xs text-[#4B5563] dark:text-[#9CA3AF] space-y-1">
          <p className="font-semibold text-[#1F2937] dark:text-[#F3F4F6] flex items-center gap-1.5 text-[11px]">
            <ShieldCheck className="w-3.5 h-3.5 text-[#10B981]" /> Auditable Citations
          </p>
          <p className="text-[10px] text-[#6B7280] dark:text-[#9CA3AF] leading-relaxed">
            Every clinical response is verified against indexed patient records.
          </p>
        </div>
      </div>

      {/* Center Main Chat Workspace */}
      <div className="flex-1 flex flex-col bg-white dark:bg-[#1B1E23] rounded-2xl border border-[#E5E7EB] dark:border-[#2F3540] overflow-hidden shadow-[0_1px_3px_0_rgba(0,0,0,0.02)] min-w-0">
        {/* Chat Header */}
        <div className="p-3.5 px-5 border-b border-[#E5E7EB] dark:border-[#2F3540] flex items-center justify-between bg-white dark:bg-[#1B1E23]">
          <div className="flex items-center space-x-3 min-w-0">
            <div className="w-8 h-8 rounded-xl bg-[#ECFDF5] dark:bg-emerald-950/40 border border-emerald-200/60 dark:border-emerald-800/40 flex items-center justify-center text-[#10B981] font-semibold text-xs shrink-0">
              CN
            </div>
            <div className="min-w-0">
              <h3 className="text-sm font-semibold text-[#1F2937] dark:text-[#F3F4F6] truncate">
                Clinical Intelligence Assistant
              </h3>
              <p className="text-[11px] text-[#6B7280] dark:text-[#9CA3AF] flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-[#10B981]" />
                Longitudinal Patient Memory Grounded
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <Badge variant="success" className="text-[10px] hidden sm:inline-flex">Citations Grounded</Badge>
            <button
              onClick={() => setShowContextPanel(!showContextPanel)}
              className={`p-1.5 px-2.5 rounded-xl border text-xs font-medium flex items-center gap-1.5 transition-colors ${
                showContextPanel
                  ? 'bg-[#ECFDF5] text-[#10B981] border-emerald-200/60 dark:bg-emerald-950/40 dark:border-emerald-800/40'
                  : 'bg-[#FAF8F5] text-[#6B7280] border-[#E5E7EB] dark:bg-[#23272E] dark:text-[#9CA3AF] dark:border-[#2F3540]'
              }`}
              title="Toggle Contextual Patient Record Panel"
            >
              <PanelRight className="w-4 h-4" />
              <span className="hidden md:inline">Patient Memory</span>
            </button>
          </div>
        </div>

        {/* Messages Stream */}
        <div className="flex-1 p-4 sm:p-5 overflow-y-auto space-y-4 sm:space-y-5 bg-[#FAF8F5]/60 dark:bg-[#121417]/50">
          {isLoadingMessages ? (
            <div className="h-full flex flex-col items-center justify-center text-center space-y-2 text-xs text-[#9CA3AF]">
              <Loader2 className="w-5 h-5 animate-spin text-[#10B981]" />
              <span>Loading conversation...</span>
            </div>
          ) : messages.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center text-center space-y-3 py-12">
              <div className="p-3.5 rounded-2xl bg-[#F3F1ED] dark:bg-[#23272E] text-[#10B981]">
                <FileQuestion className="w-6 h-6" />
              </div>
              <h4 className="text-base font-semibold text-[#1F2937] dark:text-[#F3F4F6]">
                Ask About Your Health Records
              </h4>
              <p className="text-xs text-[#6B7280] dark:text-[#9CA3AF] max-w-sm leading-relaxed">
                Query medication histories, compare lab trajectories over years, or inspect imaging reports with grounded citations.
              </p>
            </div>
          ) : (
            messages.map((msg) => <ChatBubble key={msg.id} message={msg} />)
          )}

          {isTyping && (
            <div className="flex items-center space-x-2 text-xs text-[#6B7280] dark:text-[#9CA3AF]">
              <Loader2 className="w-3.5 h-3.5 text-[#10B981] animate-spin" />
              <span>Searching medical memory and generating grounded clinical response...</span>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Suggested Prompts Bar */}
        <div className="px-4 sm:px-5 py-2 border-t border-[#E5E7EB] dark:border-[#2F3540] flex items-center gap-1.5 overflow-x-auto bg-[#FAF8F5] dark:bg-[#1B1E23]">
          <span className="text-[10px] font-semibold text-[#9CA3AF] shrink-0 flex items-center gap-1">
            <HelpCircle className="w-3 h-3" /> Prompts:
          </span>
          {suggestedPrompts.map((prompt, idx) => (
            <button
              key={idx}
              onClick={() => handleSend(prompt)}
              className="px-2.5 py-1 rounded-lg bg-white dark:bg-[#23272E] hover:bg-[#F3F1ED] dark:hover:bg-[#2D323B] border border-[#E5E7EB] dark:border-[#2F3540] text-xs text-[#4B5563] dark:text-[#D1D5DB] transition-colors shrink-0 text-left font-normal"
            >
              {prompt}
            </button>
          ))}
        </div>

        {/* Input Composer */}
        <div className="p-3.5 px-4 sm:px-5 border-t border-[#E5E7EB] dark:border-[#2F3540] bg-white dark:bg-[#1B1E23]">
          <form
            onSubmit={(e) => {
              e.preventDefault();
              handleSend();
            }}
            className="flex items-center space-x-2.5"
          >
            <div className="relative flex-1">
              <input
                type="text"
                value={inputQuery}
                onChange={(e) => setInputQuery(e.target.value)}
                placeholder="Ask a clinical question about lab values, medications, or reports..."
                className="w-full h-10 pl-3.5 pr-10 rounded-xl bg-[#FAF8F5] dark:bg-[#23272E] border border-[#E5E7EB] dark:border-[#2F3540] text-xs sm:text-sm text-[#1F2937] dark:text-[#F3F4F6] placeholder:text-[#9CA3AF] focus:outline-none focus:ring-2 focus:ring-emerald-500/15 focus:border-[#10B981] transition-all"
              />
              <button
                type="button"
                className="absolute right-3 top-2.5 text-[#9CA3AF] hover:text-[#1F2937] dark:hover:text-[#F3F4F6]"
                title="Attach reference"
              >
                <Paperclip className="w-4 h-4" />
              </button>
            </div>

            <Button
              type="submit"
              variant="primary"
              size="md"
              disabled={!inputQuery.trim() || isTyping}
              rightIcon={<Send className="w-3.5 h-3.5" />}
            >
              Ask
            </Button>
          </form>
        </div>
      </div>

      {/* Right Contextual Patient Medical Memory Panel */}
      {showContextPanel && (
        <div className="hidden xl:flex w-72 flex-col bg-white dark:bg-[#1B1E23] rounded-2xl border border-[#E5E7EB] dark:border-[#2F3540] p-4 space-y-4 shadow-[0_1px_3px_0_rgba(0,0,0,0.02)] overflow-y-auto shrink-0">
          <div className="flex items-center justify-between pb-3 border-b border-[#E5E7EB]/80 dark:border-[#2F3540]">
            <div className="flex items-center gap-2">
              <UserCheck className="w-4 h-4 text-[#10B981]" />
              <h4 className="text-xs font-semibold uppercase tracking-wider text-[#1F2937] dark:text-[#F3F4F6]">
                Patient Context
              </h4>
            </div>
            {(patient?.id || patient?.bloodGroup) && (
              <Badge variant="secondary" className="text-[10px] font-mono">
                {[patient?.id ? `ID: ${patient.id}` : null, patient?.bloodGroup ? `Blood: ${patient.bloodGroup}` : null].filter(Boolean).join(' • ')}
              </Badge>
            )}
          </div>

          {/* Active Diagnoses Snapshot */}
          <div className="space-y-2">
            <span className="text-[10px] font-semibold uppercase tracking-wider text-[#9CA3AF] flex items-center gap-1.5">
              <Activity className="w-3 h-3 text-[#B91C1C]" /> Active Conditions
            </span>
            <div className="space-y-1.5">
              {MOCK_DISEASES.filter(d => d.status === 'active' || d.status === 'chronic').slice(0, 3).map((d) => (
                <div key={d.id} className="p-2 rounded-xl bg-[#FAF8F5] dark:bg-[#23272E]/60 border border-[#E5E7EB] dark:border-[#2F3540] text-xs">
                  <div className="flex items-center justify-between font-medium text-[#1F2937] dark:text-[#F3F4F6]">
                    <span className="truncate">{d.name}</span>
                    <span className="font-mono text-[10px] text-[#9CA3AF]">{d.icdCode}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Active Medications Snapshot */}
          <div className="space-y-2">
            <span className="text-[10px] font-semibold uppercase tracking-wider text-[#9CA3AF] flex items-center gap-1.5">
              <Pill className="w-3 h-3 text-[#10B981]" /> Pharmacotherapy
            </span>
            <div className="space-y-1.5">
              {MOCK_MEDICATIONS.filter(m => m.status === 'active').slice(0, 3).map((m) => (
                <div key={m.id} className="p-2 rounded-xl bg-[#FAF8F5] dark:bg-[#23272E]/60 border border-[#E5E7EB] dark:border-[#2F3540] text-xs">
                  <p className="font-medium text-[#1F2937] dark:text-[#F3F4F6] truncate">{m.name}</p>
                  <p className="text-[10px] text-[#6B7280] dark:text-[#9CA3AF] mt-0.5">{m.dosage} • {m.frequency}</p>
                </div>
              ))}
            </div>
          </div>

          {/* Grounded Document Sources in Memory */}
          <div className="space-y-2 pt-1 border-t border-[#E5E7EB]/80 dark:border-[#2F3540]">
            <span className="text-[10px] font-semibold uppercase tracking-wider text-[#9CA3AF] flex items-center gap-1.5">
              <FileText className="w-3 h-3 text-[#10B981]" /> Grounded Records ({MOCK_REPORTS.length})
            </span>
            <div className="space-y-1.5">
              {MOCK_REPORTS.slice(0, 3).map((r) => (
                <div key={r.id} className="p-2 rounded-xl bg-[#FAF8F5] dark:bg-[#23272E]/60 border border-[#E5E7EB] dark:border-[#2F3540] text-xs">
                  <p className="font-medium text-[#1F2937] dark:text-[#F3F4F6] truncate">{r.title}</p>
                  <p className="text-[10px] text-[#6B7280] dark:text-[#9CA3AF] font-mono mt-0.5">{r.reportDate} • {r.hospitalName.split(' ')[0]}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
