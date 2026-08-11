import type { Disease } from './disease';
import type { Medication } from './medication';
import type { LabResult } from './labResult';
import type { MedicalReport } from './report';

export interface DoctorSummary {
  patientName: string;
  age: number;
  gender: string;
  generatedAt: string;
  summaryOverview: string;
  currentDiseases: Disease[];
  pastDiseases: Disease[];
  activeMedications: Medication[];
  knownAllergies: string[];
  abnormalLabs: LabResult[];
  riskFactors: string[];
  recentReports: MedicalReport[];
  timelineHighlights: string[];
}
