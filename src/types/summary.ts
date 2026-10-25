import type { Disease } from './disease';
import type { Medication } from './medication';
import type { LabResult } from './labResult';
import type { MedicalReport } from './report';

export interface ConflictingInfo {
  topic: string;
  details: string;
  recordsInvolved?: string[];
}

export interface DoctorSummary {
  patientName: string;
  age?: number;
  gender?: string;
  bloodGroup?: string;
  primaryCarePhysician?: string;
  insurance?: Record<string, any>;
  generatedAt: string;
  summaryOverview: string;
  currentDiseases: Disease[] | any[];
  pastDiseases: Disease[] | any[];
  activeMedications: Medication[] | any[];
  historicalMedications?: Medication[] | any[];
  knownAllergies: (string | any)[];
  abnormalLabs: LabResult[] | any[];
  recentLabs?: LabResult[] | any[];
  proceduresAndImaging?: any[];
  riskFactors: string[];
  recentReports: MedicalReport[] | any[];
  timelineHighlights: (string | any)[];
  conflictingInformation?: ConflictingInfo[];
  missingDataDisclosures?: string[];
  doctorQuestions?: string[];
  clinicianNotice?: string;
  shareLink?: string;
}
