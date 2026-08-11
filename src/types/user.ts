export type UserRole = 'patient' | 'doctor' | 'admin';

export interface UserPreferences {
  theme: 'light' | 'dark' | 'system';
  language: string;
  notifications: {
    email: boolean;
    sms: boolean;
    criticalAlerts: boolean;
    aiDigest: boolean;
  };
  privacy: {
    strictDataIsolation: boolean;
    localAiProcessingOnly: boolean;
    auditableLogsEnabled: boolean;
  };
}

export interface User {
  id: string;
  name: string;
  email: string;
  role: UserRole;
  avatarUrl?: string;
  phoneNumber?: string;
  preferences: UserPreferences;
  createdAt: string;
  updatedAt: string;
}
