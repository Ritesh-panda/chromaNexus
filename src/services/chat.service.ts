import { MOCK_CHAT_MESSAGES } from '../constants/mockData';
import type { ChatMessage, ConversationThread } from '../types';

export const chatService = {
  async getMessages(): Promise<ChatMessage[]> {
    await new Promise((resolve) => setTimeout(resolve, 400));
    return MOCK_CHAT_MESSAGES;
  },

  async sendMessage(query: string): Promise<ChatMessage> {
    await new Promise((resolve) => setTimeout(resolve, 1200));
    const aiResponse: ChatMessage = {
      id: `msg_ai_${Date.now()}`,
      sender: 'ai',
      text: `Based on your longitudinal health history, regarding "${query}": Your medical vault confirms your records from 2021-2026 are stable with active management for Type 2 Diabetes (Metformin 500mg) and Hypertension (Lisinopril 10mg).`,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      reasoningType: 'fact',
      citations: [
        {
          reportId: 'rep_008',
          reportTitle: 'Comprehensive Metabolic & Lipid Panel',
          date: '2026-06-15',
          excerpt: 'Glycemic control stable (HbA1c 6.7%).',
          confidenceScore: 0.98,
        },
      ],
    };
    return aiResponse;
  },

  async getThreads(): Promise<ConversationThread[]> {
    await new Promise((resolve) => setTimeout(resolve, 300));
    return [
      { id: 'th_1', title: 'Diabetes & Hypertension Medications', lastMessageDate: 'Today', messageCount: 4 },
      { id: 'th_2', title: 'Cholesterol History 2021-2026', lastMessageDate: 'Yesterday', messageCount: 6 },
      { id: 'th_3', title: 'Knee MRI Scan Discussion', lastMessageDate: '3 days ago', messageCount: 3 },
    ];
  },
};
