export type ReportCategory = 'blood_report' | 'mri' | 'ct_scan' | 'x_ray' | 'prescription' | 'discharge_summary' | 'vaccination';

export type ProcessingStatus = 'completed' | 'processing' | 'pending' | 'failed';

export interface ExtractedEntity {
  category: 'disease' | 'medication' | 'lab_value' | 'procedure' | 'allergy';
  name: string;
  confidence: number;
  value?: string;
  unit?: string;
  notes?: string;
}

export interface MedicalReport {
  id: string;
  title: string;
  fileName: string;
  fileSize: number;
  fileType: string;
  category: ReportCategory;
  hospitalName: string;
  doctorName?: string;
  reportDate: string;
  uploadDate: string;
  status: ProcessingStatus;
  confidenceScore: number; // 0 to 1
  rawText?: string;
  summary?: string;
  extractedEntities: ExtractedEntity[];
  fileUrl?: string;
}
