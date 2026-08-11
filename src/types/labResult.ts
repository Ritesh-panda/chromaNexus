export type LabStatus = 'normal' | 'high' | 'low' | 'critical';

export interface LabResult {
  id: string;
  testName: string;
  category: 'lipid_panel' | 'metabolic' | 'cbc' | 'thyroid' | 'vitamin' | 'other';
  value: number | string;
  unit: string;
  referenceRange: string;
  status: LabStatus;
  testDate: string;
  sourceReportId?: string;
  hospitalName?: string;
}
