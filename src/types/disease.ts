export type DiseaseStatus = 'active' | 'resolved' | 'chronic' | 'in_remission';

export interface Disease {
  id: string;
  name: string;
  icdCode?: string;
  status: DiseaseStatus;
  diagnosedDate: string;
  resolvedDate?: string;
  treatingDoctor?: string;
  sourceReportId?: string;
  notes?: string;
}
