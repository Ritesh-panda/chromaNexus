import { api } from './axios';

export interface PurgeScopeCounts {
  reports_count: number;
  documents_count: number;
  lab_results_count: number;
  medications_count: number;
  conditions_count: number;
  allergies_count: number;
  timeline_events_count: number;
  summaries_count: number;
  questions_count: number;
  chroma_vectors_count: number;
  files_to_delete_count: number;
}

export interface PurgePreviewResponse {
  confirmation_token: string;
  expires_at: string;
  patient_id: string;
  scope: PurgeScopeCounts;
  confirmation_phrase_required: string;
  exclusions: string[];
  warning: string;
}

export interface PurgeExecutionResponse {
  success: boolean;
  status: string;
  patient_id: string;
  summary: {
    documents_deleted: number;
    reports_deleted: number;
    lab_results_deleted: number;
    medications_deleted: number;
    conditions_deleted: number;
    allergies_deleted: number;
    timeline_events_deleted: number;
    summaries_deleted: number;
    questions_deleted: number;
    chroma_vectors_deleted: number;
    files_deleted: number;
    failed_file_deletions: string[];
  };
  audit_event_id: string;
  executed_at: string;
  exclusions_disclaimer: string;
}

export interface AuditLogItem {
  id: string;
  timestamp: string;
  actor_id: string | null;
  patient_id: string | null;
  action: string;
  outcome: string;
  resource_type: string | null;
  resource_id: string | null;
  details: Record<string, unknown> | null;
}

export const governanceService = {
  /**
   * Downloads the official HL7 FHIR R4 JSON bundle for the authenticated patient
   */
  async exportFhirBundle(): Promise<void> {
    const response = await api.get('/fhir/export', {
      responseType: 'blob',
    });

    const blob = new Blob([response.data], { type: 'application/fhir+json' });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    
    // Extract filename from header or use default
    const contentDisposition = response.headers['content-disposition'];
    let filename = 'chronanexus_fhir_r4_bundle.json';
    if (contentDisposition) {
      const match = contentDisposition.match(/filename="?([^"]+)"?/);
      if (match && match[1]) {
        filename = match[1];
      }
    }
    
    link.setAttribute('download', filename);
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
  },

  /**
   * Requests a safe purge preview with scoped counts and 15-minute confirmation token
   */
  async requestPurgePreview(): Promise<PurgePreviewResponse> {
    const response = await api.post<PurgePreviewResponse>('/patients/me/purge/request');
    return response.data;
  },

  /**
   * Confirms and executes irreversible patient data purge across relational, file, and vector stores
   */
  async confirmPurge(token: string, phrase: string): Promise<PurgeExecutionResponse> {
    const response = await api.post<PurgeExecutionResponse>('/patients/me/purge/confirm', {
      confirmation_token: token,
      confirmation_phrase: phrase,
    });
    return response.data;
  },

  /**
   * Retrieves security audit logs for the authenticated patient/actor
   */
  async getAuditLogs(limit = 50): Promise<AuditLogItem[]> {
    const response = await api.get<{ logs: AuditLogItem[] }>('/audit/logs', {
      params: { limit },
    });
    return response.data.logs || [];
  },
};

export default governanceService;
