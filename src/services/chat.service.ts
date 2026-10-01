import { api } from './axios';
import { MOCK_CHAT_MESSAGES, MOCK_REPORTS } from '@/constants/mockData';
import type { ChatMessage, ConversationThread, Citation } from '@/types';

export const chatService = {
  async getMessages(conversationId?: string): Promise<ChatMessage[]> {
    try {
      const convId = conversationId || 'conv_default_001';
      const response = await api.get<{ messages: ChatMessage[] }>(`/chat/conversations/${convId}`);
      if (response.data && response.data.messages && response.data.messages.length > 0) {
        return response.data.messages;
      }
    } catch {
      // Fallback
    }
    await new Promise((resolve) => setTimeout(resolve, 300));
    return MOCK_CHAT_MESSAGES;
  },

  async sendMessage(query: string, conversationId?: string): Promise<ChatMessage> {
    try {
      const convId = conversationId || 'conv_default_001';
      const response = await api.post<ChatMessage>(`/chat/conversations/${convId}/messages`, {
        query,
      });
      if (response.data && response.data.text) {
        return response.data;
      }
    } catch {
      // Fallback to local clinical intent matching
    }

    await new Promise((resolve) => setTimeout(resolve, 600));
    const lowerQuery = query.toLowerCase();

    let text = '';
    let reasoningType: 'fact' | 'inference' = 'fact';
    let citations: Citation[] = [];

    if (lowerQuery.includes('cholesterol') || lowerQuery.includes('lipid')) {
      text = 'Your highest recorded total cholesterol was 242 mg/dL on June 12, 2021 (Quest Diagnostics lipid panel). Through dietary intervention and initiation of Atorvastatin 10mg QD, your levels decreased to 198 mg/dL as of your most recent Comprehensive Metabolic & Lipid Panel on June 15, 2026.';
      reasoningType = 'fact';
      citations = [
        {
          reportId: 'rep_002',
          reportTitle: 'Lipid Profile & Glucose Screening',
          date: '2021-06-12',
          excerpt: 'Total Cholesterol: 242 mg/dL (High, Ref: <200). Fasting Glucose: 104 mg/dL.',
          confidenceScore: 0.99,
        },
        {
          reportId: 'rep_008',
          reportTitle: 'Comprehensive Metabolic & Lipid Panel',
          date: '2026-06-15',
          excerpt: 'Total Cholesterol: 198 mg/dL (Normal). LDL: 112 mg/dL, HDL: 48 mg/dL.',
          confidenceScore: 0.98,
        },
      ];
    } else if (lowerQuery.includes('mri') || lowerQuery.includes('knee') || lowerQuery.includes('meniscus')) {
      text = 'According to your MRI report dated August 10, 2022 from St. Jude Diagnostic Imaging: A 3.0T MRI of your Right Knee demonstrated a Grade II signal alteration of the posterior horn of the medial meniscus without displaced flap tear. Cruciate and collateral ligaments were intact. Conservative physical therapy was recommended.';
      reasoningType = 'fact';
      citations = [
        {
          reportId: 'rep_003',
          reportTitle: 'MRI Right Knee Joint',
          date: '2022-08-10',
          excerpt: 'Grade II degenerative signal medial meniscus posterior horn. No displaced tear.',
          confidenceScore: 0.97,
        },
      ];
    } else if (lowerQuery.includes('blood pressure') || lowerQuery.includes('hypertension') || lowerQuery.includes('lisinopril')) {
      text = 'For Essential Hypertension (diagnosed November 2023), you are currently taking Lisinopril 10mg once daily (QD) prescribed by Dr. Sarah Jenkins. Blood pressure readings stabilized from 145/92 mmHg at diagnosis to 124/80 mmHg in recent checkups.';
      reasoningType = 'fact';
      citations = [
        {
          reportId: 'rep_004',
          reportTitle: 'Clinical Encounter & Rx — Hypertension Initial',
          date: '2023-11-04',
          excerpt: 'Dx: Essential (primary) hypertension (I10). Rx: Lisinopril 10mg PO QD #30.',
          confidenceScore: 0.99,
        },
        {
          reportId: 'rep_007',
          reportTitle: 'Cardiovascular Risk & Echo Evaluation',
          date: '2025-11-20',
          excerpt: 'Resting BP: 124/80 mmHg. Continued Lisinopril 10mg QD.',
          confidenceScore: 0.96,
        },
      ];
    } else if (lowerQuery.includes('hba1c') || lowerQuery.includes('trajectory') || lowerQuery.includes('diabetes') || lowerQuery.includes('metformin')) {
      text = 'Your longitudinal HbA1c trajectory shows notable glycemic improvement: It peaked at 7.2% in September 2023 when Type 2 Diabetes was diagnosed, and progressively improved to 6.9% (2024), 6.8% (2025), and reached 6.7% in your June 2026 panel under continuous Metformin 500mg BID therapy.';
      reasoningType = 'fact';
      citations = [
        {
          reportId: 'rep_005',
          reportTitle: 'Comprehensive Metabolic Panel & HbA1c',
          date: '2023-09-18',
          excerpt: 'HbA1c: 7.2% (High, Ref: 4.0 - 5.6%). Fasting Plasma Glucose: 142 mg/dL.',
          confidenceScore: 0.99,
        },
        {
          reportId: 'rep_008',
          reportTitle: 'Comprehensive Metabolic & Lipid Panel',
          date: '2026-06-15',
          excerpt: 'HbA1c: 6.7% (Improved). Fasting Glucose: 128 mg/dL.',
          confidenceScore: 0.98,
        },
      ];
    } else if (lowerQuery.includes('surgery') || lowerQuery.includes('surgeries') || lowerQuery.includes('procedure') || lowerQuery.includes('operation')) {
      text = 'Based on your 8 indexed records spanning 2019-2026, no surgical procedures or operative interventions were recorded. Your hospital admissions were medical management (Dengue Fever hospitalization at Metro General in 2019) and conservative orthopedic physical therapy for knee meniscus strain in 2022.';
      reasoningType = 'fact';
      citations = [
        {
          reportId: 'rep_001',
          reportTitle: 'Inpatient Discharge Summary — Dengue Hemorrhagic',
          date: '2019-10-14',
          excerpt: 'Medical inpatient stay: IV fluid hydration and platelet monitoring. No surgical intervention required.',
          confidenceScore: 0.95,
        },
      ];
    } else if (lowerQuery.includes('medicines') || lowerQuery.includes('last year') || lowerQuery.includes('medication')) {
      text = 'Reviewing your prescriptions: In 2025, your active medication regimen consisted of Metformin 500mg BID (for Type 2 Diabetes), Lisinopril 10mg QD (for Hypertension), and Atorvastatin 10mg QD (for Hyperlipidemia). Additionally, in 2020 you completed a 12-week high-dose course of Cholecalciferol (Vitamin D3 60,000 IU/week).';
      reasoningType = 'fact';
      citations = [
        {
          reportId: 'rep_006',
          reportTitle: 'Follow-Up Prescription & Endocrine Review',
          date: '2024-05-10',
          excerpt: 'Rx: Metformin 500mg BID, Lisinopril 10mg QD, Atorvastatin 10mg QD.',
          confidenceScore: 0.98,
        },
      ];
    } else {
      text = `Based on your longitudinal health history regarding "${query}": Your medical vault confirms your records from 2019-2026 are stable with active management for Type 2 Diabetes (Metformin 500mg BID) and Hypertension (Lisinopril 10mg QD). All 8 clinical reports are indexed in your patient memory graph.`;
      reasoningType = 'inference';
      citations = [
        {
          reportId: MOCK_REPORTS[0]?.id || 'rep_008',
          reportTitle: MOCK_REPORTS[0]?.title || 'Comprehensive Metabolic & Lipid Panel',
          date: MOCK_REPORTS[0]?.reportDate || '2026-06-15',
          excerpt: 'Patient memory graph indexed across 8 connected encounters.',
          confidenceScore: 0.94,
        },
      ];
    }

    const aiResponse: ChatMessage = {
      id: `msg_ai_${Date.now()}`,
      sender: 'ai',
      text,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      reasoningType,
      citations,
    };
    return aiResponse;
  },

  async getThreads(): Promise<ConversationThread[]> {
    try {
      const response = await api.get<{ threads: ConversationThread[] }>('/chat/conversations');
      if (response.data && response.data.threads && response.data.threads.length > 0) {
        return response.data.threads;
      }
    } catch {
      // Fallback
    }
    await new Promise((resolve) => setTimeout(resolve, 200));
    return [
      { id: 'conv_default_001', title: 'Diabetes & Hypertension Medications', lastMessageDate: 'Today', messageCount: 4 },
      { id: 'th_2', title: 'Cholesterol History 2021-2026', lastMessageDate: 'Yesterday', messageCount: 6 },
      { id: 'th_3', title: 'Knee MRI Scan Discussion', lastMessageDate: '3 days ago', messageCount: 3 },
    ];
  },
};


