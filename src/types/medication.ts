export type MedicationStatus = 'active' | 'discontinued' | 'as_needed' | 'completed';

export interface Medication {
  id: string;
  name: string;
  dosage: string;
  frequency: string;
  route?: string; // oral, IV, topical
  startDate: string;
  endDate?: string;
  status: MedicationStatus;
  prescribingDoctor?: string;
  indication?: string; // e.g. "Hypertension", "Vitamin D Deficiency"
  sourceReportId?: string;
}
