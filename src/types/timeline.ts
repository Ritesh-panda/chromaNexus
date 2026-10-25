export type TimelineEventType = 
  | 'diagnosis'
  | 'medication_start'
  | 'medication_stop'
  | 'lab_test'
  | 'imaging'
  | 'surgery'
  | 'vaccination'
  | 'hospital_visit'
  | 'medical_report'
  | 'symptom';

export interface TimelineEvent {
  id: string;
  date: string;
  year: number;
  title: string;
  description: string;
  type: TimelineEventType;
  severity?: 'low' | 'medium' | 'high' | 'critical';
  doctorName?: string;
  facility?: string;
  sourceReportId?: string;
  sourceReportTitle?: string;
  connectedEntities?: {
    diseases?: string[];
    medications?: string[];
    labResults?: string[];
  };
  uploadDate?: string;
  isUnknownDate?: boolean;
  hasConflict?: boolean;
  conflictDetails?: string;
}

export interface TimelineSummary {
  totalEvents: number;
  eventTypes: string[];
  facilities: string[];
  years: number[];
  dateRange: {
    earliest: string | null;
    latest: string | null;
  };
}
