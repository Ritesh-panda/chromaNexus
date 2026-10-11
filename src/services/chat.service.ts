import { api } from './axios';
import { MOCK_CHAT_MESSAGES, MOCK_REPORTS } from '@/constants/mockData';
import type { ChatMessage, ConversationThread, Citation } from '@/types';

export const chatService = {
  async getThreads(): Promise<ConversationThread[]> {
    const response = await api.get<ConversationThread[]>('/chat/conversations');
    return response.data;
  },

  async createConversation(title?: string): Promise<ConversationThread> {
    const response = await api.post<ConversationThread>('/chat/conversations', { title });
    return response.data;
  },

  async getMessages(conversationId: string): Promise<ChatMessage[]> {
    const response = await api.get<ChatMessage[]>(`/chat/conversations/${conversationId}/messages`);
    return response.data;
  },

  async sendMessage(query: string, conversationId: string): Promise<ChatMessage> {
    const response = await api.post<ChatMessage>(
      `/chat/conversations/${conversationId}/messages`,
      { text: query },
      { timeout: 90000 }
    );
    return response.data;
  },
};



