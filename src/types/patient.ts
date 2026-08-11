export interface EmergencyContact {
  name: string;
  relationship: string;
  phone: string;
}

export interface InsuranceProvider {
  providerName: string;
  policyNumber: string;
  groupNumber: string;
  validUntil: string;
}

export interface Patient {
  id: string;
  userId: string;
  dateOfBirth: string;
  gender: 'male' | 'female' | 'other';
  bloodGroup: string;
  heightCm: number;
  weightKg: number;
  primaryCarePhysician: string;
  emergencyContact: EmergencyContact;
  insurance?: InsuranceProvider;
  knownAllergies: string[];
}
