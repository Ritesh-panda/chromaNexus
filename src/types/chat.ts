export interface Citation {
  reportId: string;
  reportTitle: string;
  excerpt: string;
  date: string;
  confidenceScore: number;
}

export interface ChatMessage {
  id: string;
  sender: 'user' | 'ai';
  text: string;
  timestamp: string;
  citations?: Citation[];
  reasoningType?: 'fact' | 'inference';
  isTyping?: boolean;
}

export interface ConversationThread {
  id: string;
  title: string;
  lastMessageDate: string;
  messageCount: number;
}
