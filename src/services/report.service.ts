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

export interface GetReportsParams {
  category?: string;
  hospital?: string;
  search?: string;
  status?: string;
  startDate?: string;
  endDate?: string;
  sortBy?: 'clinical_date' | 'upload_date';
  sortOrder?: 'asc' | 'desc';
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
  async getReports(paramsOrCategory?: string | GetReportsParams, search?: string): Promise<MedicalReport[]> {
    try {
      const params: Record<string, string> = {};
      if (typeof paramsOrCategory === 'string') {
        if (paramsOrCategory && paramsOrCategory !== 'all') params.category = paramsOrCategory;
        if (search) params.search = search;
      } else if (paramsOrCategory) {
        if (paramsOrCategory.category && paramsOrCategory.category !== 'all') params.category = paramsOrCategory.category;
        if (paramsOrCategory.hospital && paramsOrCategory.hospital !== 'all') params.hospital = paramsOrCategory.hospital;
        if (paramsOrCategory.search) params.search = paramsOrCategory.search;
        if (paramsOrCategory.status && paramsOrCategory.status !== 'all') params.status = paramsOrCategory.status;
        if (paramsOrCategory.startDate) params.start_date = paramsOrCategory.startDate;
        if (paramsOrCategory.endDate) params.end_date = paramsOrCategory.endDate;
        if (paramsOrCategory.sortBy) params.sort_by = paramsOrCategory.sortBy;
        if (paramsOrCategory.sortOrder) params.sort_order = paramsOrCategory.sortOrder;
      }

      const response = await api.get('/reports', { params });
      return response.data;
    } catch {
      let reports = [...MOCK_REPORTS];
      const category = typeof paramsOrCategory === 'string' ? paramsOrCategory : paramsOrCategory?.category;
      const q = (typeof paramsOrCategory === 'string' ? search : paramsOrCategory?.search)?.toLowerCase();
      const status = typeof paramsOrCategory === 'object' ? paramsOrCategory?.status : undefined;
      const hospital = typeof paramsOrCategory === 'object' ? paramsOrCategory?.hospital : undefined;
      const sortBy = typeof paramsOrCategory === 'object' ? paramsOrCategory?.sortBy : 'clinical_date';
      const sortOrder = typeof paramsOrCategory === 'object' ? paramsOrCategory?.sortOrder : 'desc';

      if (category && category !== 'all') {
        reports = reports.filter((r) => r.category === category);
      }
      if (hospital && hospital !== 'all') {
        reports = reports.filter((r) => r.hospitalName.toLowerCase().includes(hospital.toLowerCase()));
      }
      if (status && status !== 'all') {
        reports = reports.filter((r) => r.status === status);
      }
      if (q) {
        reports = reports.filter(
          (r) =>
            r.title.toLowerCase().includes(q) ||
            r.hospitalName.toLowerCase().includes(q) ||
            (r.summary && r.summary.toLowerCase().includes(q))
        );
      }

      // Sort
      reports.sort((a, b) => {
        const valA = sortBy === 'upload_date' ? a.uploadDate || a.reportDate : a.reportDate;
        const valB = sortBy === 'upload_date' ? b.uploadDate || b.reportDate : b.reportDate;
        return sortOrder === 'asc' ? valA.localeCompare(valB) : valB.localeCompare(valA);
      });

      return reports;
    }
  },

  async getFacilities(): Promise<string[]> {
    try {
      const response = await api.get('/reports/facilities');
      return response.data;
    } catch {
      const unique = Array.from(new Set(MOCK_REPORTS.map((r) => r.hospitalName)));
      return unique;
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
      return false;
    }
  },
};
