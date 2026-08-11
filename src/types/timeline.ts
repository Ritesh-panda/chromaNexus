export type TimelineEventType = 
  | 'diagnosis'
  | 'medication_start'
  | 'medication_stop'
  | 'lab_test'
  | 'imaging'
  | 'surgery'
  | 'vaccination'
  | 'hospital_visit'
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
}
