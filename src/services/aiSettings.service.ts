import { api } from './axios';

export interface AIModeConfig {
  mode: 'online' | 'offline';
  active_provider: string;
  online_model: string;
  offline_model: string;
  groq_configured: boolean;
  status: string;
}

export const aiSettingsService = {
  async getAIMode(): Promise<AIModeConfig> {
    try {
      const res = await api.get<AIModeConfig>('/settings/ai-mode');
      return res.data;
    } catch {
      return {
        mode: 'online',
        active_provider: 'Groq LPU (Cloud)',
        online_model: 'openai/gpt-oss-120b',
        offline_model: 'llama3.2:3b',
        groq_configured: true,
        status: 'Operational',
      };
    }
  },

  async setAIMode(mode: 'online' | 'offline'): Promise<AIModeConfig> {
    const res = await api.post<AIModeConfig>('/settings/ai-mode', { mode });
    return res.data;
  },
};
