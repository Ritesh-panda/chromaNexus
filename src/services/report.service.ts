import { MOCK_REPORTS } from '@/constants/mockData';
import type { MedicalReport, ReportCategory } from '@/types';

export interface UploadReportParams {
  file: File;
  category: ReportCategory;
  hospitalName?: string;
  doctorName?: string;
  reportDate?: string;
}

export const reportService = {
  async getReports(category?: string, search?: string): Promise<MedicalReport[]> {
    await new Promise((resolve) => setTimeout(resolve, 500));
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
  },

  async getReportById(id: string): Promise<MedicalReport | null> {
    await new Promise((resolve) => setTimeout(resolve, 300));
    const report = MOCK_REPORTS.find((r) => r.id === id);
    return report || null;
  },

  async uploadReport(params: UploadReportParams): Promise<MedicalReport> {
    await new Promise((resolve) => setTimeout(resolve, 1500));
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
  },

  async deleteReport(id: string): Promise<boolean> {
    await new Promise((resolve) => setTimeout(resolve, 400));
    return true;
  },
};
