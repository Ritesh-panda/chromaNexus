import { api } from './axios';
import type { ChatMessage, ConversationThread } from '@/types';

export const chatService = {
  async getThreads(): Promise<ConversationThread[]> {
    try {
      const response = await api.get<ConversationThread[]>('/chat/conversations');
      return response.data;
    } catch {
      return [];
    }
  },

  async createConversation(title?: string): Promise<ConversationThread> {
    try {
      const response = await api.post<ConversationThread>('/chat/conversations', { title });
      return response.data;
    } catch {
      return {
        id: `conv_${Date.now()}`,
        title: title || 'New Clinical Inquiry',
        lastMessageDate: new Date().toISOString(),
        messageCount: 0,
      };
    }
  },

  async getMessages(conversationId: string): Promise<ChatMessage[]> {
    try {
      const response = await api.get<ChatMessage[]>(`/chat/conversations/${conversationId}/messages`);
      return response.data;
    } catch {
      return [];
    }
  },

  async sendMessage(query: string, conversationId: string): Promise<ChatMessage> {
    try {
      const response = await api.post<ChatMessage>(
        `/chat/conversations/${conversationId}/messages`,
        { text: query },
        { timeout: 90000 }
      );
      return response.data;
    } catch (err: unknown) {
      const isNetworkError =
        err && typeof err === 'object' && ('code' in err && (err as any).code === 'ERR_NETWORK' || 'message' in err && String((err as any).message).includes('Network Error'));
      if (isNetworkError) {
        throw new Error('Backend server is not running on http://localhost:8000. Please start the FastAPI backend server.');
      }
      throw err;
    }
  },
};



