export type NotificationType = 'report_processed' | 'abnormal_lab' | 'medication_reminder' | 'system';

export interface Notification {
  id: string;
  title: string;
  message: string;
  timestamp: string;
  read: boolean;
  type: NotificationType;
  actionUrl?: string;
}
