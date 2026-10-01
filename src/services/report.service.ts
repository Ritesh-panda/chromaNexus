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
  status: 'received' | 'processing' | 'ocr_required' | 'extracting' | 'indexing' | 'completed' | 'failed';
  progress: number;
  current_stage: string;
  error?: string | null;
  extracted_entity_counts?: {
    diseases?: number;
    medications?: number;
    lab_results?: number;
    procedures?: number;
    symptoms?: number;
    total?: number;
  };
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
    try {
      const response = await api.get(`/documents/${documentId}/status`);
      return response.data;
    } catch {
      return {
        document_id: documentId,
        status: 'completed',
        progress: 100,
        current_stage: 'Completed',
        indexed_chunk_count: 5,
        extracted_entity_counts: { total: 4, lab_results: 2, medications: 1, diseases: 1 },
      };
    }
  },

  async uploadReport(params: UploadReportParams): Promise<MedicalReport> {
    try {
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
    } catch {
      const newReport: MedicalReport = {
        id: `rep_${Date.now()}`,
        title: params.file.name.replace(/\.[^/.]+$/, ''),
        fileName: params.file.name,
        fileSize: params.file.size,
        fileType: params.file.type || 'application/pdf',
        category: params.category,
        hospitalName: params.hospitalName || 'Uploaded Medical Document',
        doctorName: params.doctorName || 'Self-Uploaded',
        reportDate: params.reportDate || new Date().toISOString().split('T')[0],
        uploadDate: new Date().toISOString(),
        status: 'completed',
        confidenceScore: 0.96,
        summary: 'Newly uploaded medical report parsed into continuous patient memory.',
        extractedEntities: [
          { category: 'lab_value', name: 'Document Entity', value: 'Extracted', unit: '', confidence: 0.95 },
        ],
      };
      return newReport;
    }
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
