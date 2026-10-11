import api from '@/services/axios';
import { MOCK_REPORTS } from '@/constants/mockData';
import type { MedicalReport, ReportCategory } from '@/types';

export interface UploadReportParams {
  file: File;
  category: ReportCategory;
  hospitalName?: string;
  doctorName?: string;
  reportDate?: string;
}

export interface DocumentIngestionStatus {
  document_id: string;
  status:
    | 'RECEIVED'
    | 'PROCESSING'
    | 'OCR_REQUIRED'
    | 'EXTRACTING'
    | 'INDEXING'
    | 'COMPLETED'
    | 'FAILED'
    | 'received'
    | 'processing'
    | 'ocr_required'
    | 'extracting'
    | 'indexing'
    | 'completed'
    | 'failed';
  progress_percent?: number;
  progress?: number;
  current_stage: string;
  error_message?: string | null;
  error?: string | null;
  extracted_counts?: {
    diseases?: number;
    medications?: number;
    lab_results?: number;
    procedures?: number;
    symptoms?: number;
    total?: number;
  };
  extracted_entity_counts?: {
    diseases?: number;
    medications?: number;
    lab_results?: number;
    procedures?: number;
    symptoms?: number;
    total?: number;
  };
  indexed_chunks_count?: number;
  indexed_chunk_count?: number;
  report_id?: string | null;
}

export const reportService = {
  async getReports(category?: string, search?: string): Promise<MedicalReport[]> {
    try {
      const params: Record<string, string> = {};
      if (category && category !== 'all') params.category = category;
      if (search) params.search = search;
      const response = await api.get('/reports', { params });
      return response.data;
    } catch {
      let reports = [...MOCK_REPORTS];
      if (category && category !== 'all') {
        reports = reports.filter((r) => r.category === category);
      }
      if (search) {
        const q = search.toLowerCase();
        reports = reports.filter(
          (r) =>
            r.title.toLowerCase().includes(q) ||
            r.hospitalName.toLowerCase().includes(q) ||
            (r.summary && r.summary.toLowerCase().includes(q))
        );
      }
      return reports;
    }
  },

  async getReportById(id: string): Promise<MedicalReport | null> {
    try {
      const response = await api.get(`/reports/${id}`);
      return response.data;
    } catch {
      const report = MOCK_REPORTS.find((r) => r.id === id);
      return report || null;
    }
  },

  async getIngestionStatus(documentId: string): Promise<DocumentIngestionStatus> {
    const response = await api.get(`/documents/${documentId}/status`);
    return response.data;
  },

  async uploadReport(params: UploadReportParams): Promise<MedicalReport> {
    const formData = new FormData();
    formData.append('file', params.file);
    formData.append('category', params.category);
    if (params.hospitalName) formData.append('hospital_name', params.hospitalName);
    if (params.doctorName) formData.append('doctor_name', params.doctorName);
    if (params.reportDate) formData.append('report_date', params.reportDate);

    const response = await api.post('/documents/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },

  async deleteReport(id: string): Promise<boolean> {
    try {
      await api.delete(`/reports/${id}`);
      return true;
    } catch {
      return true;
    }
  },
};
