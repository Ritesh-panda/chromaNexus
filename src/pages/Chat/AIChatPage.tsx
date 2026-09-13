import React, { useState, useRef, useEffect } from 'react';
import { ChatBubble } from '@/components/cards/ChatBubble';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { MOCK_CHAT_MESSAGES } from '@/constants/mockData';
import type { ChatMessage, ConversationThread } from '@/types';
import { chatService } from '@/services/chat.service';
import {
  Bot,
  Send,
  Plus,
  MessageSquare,
  Sparkles,
  ShieldCheck,
  HelpCircle,
  Paperclip
} from 'lucide-react';

export const AIChatPage: React.FC = () => {
  const [messages, setMessages] = useState<ChatMessage[]>(MOCK_CHAT_MESSAGES);
  const [threads, setThreads] = useState<ConversationThread[]>([
    { id: 'th_1', title: 'Diabetes & Hypertension Medications', lastMessageDate: 'Today', messageCount: 4 },
    { id: 'th_2', title: 'Cholesterol History 2021-2026', lastMessageDate: 'Yesterday', messageCount: 6 },
    { id: 'th_3', title: 'Knee MRI Scan Discussion', lastMessageDate: '3 days ago', messageCount: 3 },
  ]);
  const [activeThreadId, setActiveThreadId] = useState('th_1');
  const [inputQuery, setInputQuery] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const suggestedPrompts = [
    'What medicines did I take for high blood pressure?',
    'When was my highest cholesterol reading?',
    'Show all MRI reports and meniscus findings.',
    'Summarize my HbA1c trajectory from 2023 to 2026.',
  ];

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isTyping]);

  const handleSend = async (textToSend?: string) => {
    const query = textToSend || inputQuery;
    if (!query.trim()) return;

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
      const response = await chatService.sendMessage(query);
      setMessages((prev) => [...prev, response]);
    } finally {
      setIsTyping(false);
    }
  };

  return (
    <div className="h-[calc(100vh-8rem)] flex gap-6 pb-4">
      {/* Left Threads Sidebar */}
      <div className="hidden lg:flex w-72 flex-col glass-card rounded-3xl border border-slate-200 dark:border-slate-800 p-4 space-y-4">
        <Button
          variant="primary"
          className="w-full justify-start"
          leftIcon={<Plus className="w-4 h-4" />}
          onClick={() => {
            const newTh: ConversationThread = {
              id: `th_${Date.now()}`,
              title: 'New Medical Inquiry',
              lastMessageDate: 'Just now',
              messageCount: 0,
            };
            setThreads([newTh, ...threads]);
            setActiveThreadId(newTh.id);
            setMessages([]);
          }}
        >
          New Clinical Conversation
        </Button>

        <div className="space-y-1 flex-1 overflow-y-auto">
          <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400 px-2 block mb-2">
            Conversation History
          </span>
          {threads.map((th) => (
            <button
              key={th.id}
              onClick={() => setActiveThreadId(th.id)}
              className={`w-full flex items-center justify-between p-3 rounded-2xl text-left text-xs font-semibold transition-all ${
                activeThreadId === th.id
                  ? 'bg-blue-50 dark:bg-blue-950/60 text-blue-600 dark:text-blue-400 border border-blue-200 dark:border-blue-800/40'
                  : 'text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800/60'
              }`}
            >
              <span className="truncate flex items-center gap-2">
                <MessageSquare className="w-3.5 h-3.5 shrink-0" /> {th.title}
              </span>
              <span className="text-[10px] opacity-60 shrink-0">{th.lastMessageDate}</span>
            </button>
          ))}
        </div>

        <div className="p-3 rounded-2xl bg-emerald-50 dark:bg-emerald-950/30 border border-emerald-200 dark:border-emerald-900/30 text-[11px] text-emerald-800 dark:text-emerald-300 space-y-1">
          <p className="font-bold flex items-center gap-1"><ShieldCheck className="w-3.5 h-3.5" /> Auditable AI Reasoning</p>
          <p className="text-[10px] text-slate-500">Every response is strictly grounded in your uploaded medical reports.</p>
        </div>
      </div>

      {/* Main Chat Interface */}
      <div className="flex-1 flex flex-col glass-card rounded-3xl border border-slate-200 dark:border-slate-800 overflow-hidden">
        {/* Chat Header */}
        <div className="p-4 px-6 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between bg-white/40 dark:bg-[#131B2E]/40">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-2xl bg-gradient-to-tr from-blue-600 to-emerald-400 flex items-center justify-center text-white font-bold shadow-md shadow-blue-500/20">
              <Bot className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2">
                ChronaNexus AI Clinical Assistant
              </h3>
              <p className="text-xs text-slate-400 flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                Grounded in 8 Medical Documents • Local Privacy Enabled
              </p>
            </div>
          </div>
          <Badge variant="success">Citation Reasoning Mode</Badge>
        </div>

        {/* Messages Stream */}
        <div className="flex-1 p-6 overflow-y-auto space-y-6">
          {messages.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center text-center space-y-4 py-12">
              <div className="p-4 rounded-full bg-blue-100 dark:bg-blue-900/40 text-blue-600">
                <Sparkles className="w-8 h-8" />
              </div>
              <h4 className="text-lg font-bold text-slate-900 dark:text-slate-100">Ask Anything About Your Health History</h4>
              <p className="text-xs text-slate-500 max-w-sm">
                Query dosages, compare lab results across years, or ask about MRI findings with grounded source citations.
              </p>
            </div>
          ) : (
            messages.map((msg) => <ChatBubble key={msg.id} message={msg} />)
          )}

          {isTyping && (
            <div className="flex items-center space-x-3 text-xs text-slate-400 animate-pulse">
              <Bot className="w-4 h-4 text-blue-500" />
              <span>ChronaNexus AI is reasoning over your medical memory graph...</span>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Suggested Prompt Chips */}
        <div className="px-6 py-2 border-t border-slate-100 dark:border-slate-800/80 flex items-center gap-2 overflow-x-auto bg-slate-50/50 dark:bg-[#0B0F19]/40">
          <span className="text-[11px] font-bold text-slate-400 shrink-0 flex items-center gap-1">
            <HelpCircle className="w-3 h-3" /> Prompts:
          </span>
          {suggestedPrompts.map((prompt, idx) => (
            <button
              key={idx}
              onClick={() => handleSend(prompt)}
              className="px-3 py-1.5 rounded-xl bg-white dark:bg-slate-800/80 hover:bg-blue-50 dark:hover:bg-blue-950/60 border border-slate-200 dark:border-slate-700 text-xs font-semibold text-slate-700 dark:text-slate-300 transition-colors shrink-0"
            >
              {prompt}
            </button>
          ))}
        </div>

        {/* Input Bar */}
        <div className="p-4 px-6 border-t border-slate-200 dark:border-slate-800 bg-white/60 dark:bg-[#131B2E]/60">
          <form
            onSubmit={(e) => {
              e.preventDefault();
              handleSend();
            }}
            className="flex items-center space-x-3"
          >
            <div className="relative flex-1">
              <input
                type="text"
                value={inputQuery}
                onChange={(e) => setInputQuery(e.target.value)}
                placeholder="Ask about medications, lab trends, or medical history..."
                className="w-full h-12 pl-4 pr-10 rounded-2xl bg-slate-100 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700/60 text-sm text-slate-900 dark:text-slate-100 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500/50"
              />
              <button
                type="button"
                className="absolute right-3.5 top-3.5 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200"
              >
                <Paperclip className="w-5 h-5" />
              </button>
            </div>

            <Button
              type="submit"
              variant="primary"
              size="lg"
              disabled={!inputQuery.trim() || isTyping}
              rightIcon={<Send className="w-4 h-4" />}
            >
              Ask AI
            </Button>
          </form>
        </div>
      </div>
    </div>
  );
};
