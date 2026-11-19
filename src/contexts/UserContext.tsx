import React, { createContext, useContext, useState, useEffect } from 'react';
import type { Patient } from '@/types';
import { MOCK_PATIENT } from '@/constants/mockData';
import { patientService } from '@/services/patient.service';
import { useAuth } from '@/contexts/AuthContext';

interface UserContextType {
  patient: Patient;
  updatePatient: (updated: Partial<Patient>) => void;
  refreshProfile: () => Promise<void>;
}

const UserContext = createContext<UserContextType | undefined>(undefined);

export const UserProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { user } = useAuth();
  const isDemo = user?.email === 'alex.vance@example.com';

  const createCleanPatient = (uId?: string): Patient => ({
    id: uId ? `pat_${uId}` : '',
    userId: uId || '',
    dateOfBirth: '',
    gender: 'other',
    bloodGroup: '',
    heightCm: 0,
    weightKg: 0,
    primaryCarePhysician: '',
    emergencyContact: {
      name: '',
      relationship: '',
      phone: ''
    },
    knownAllergies: []
  });

  const [patient, setPatient] = useState<Patient>(isDemo ? MOCK_PATIENT : createCleanPatient(user?.id));

  const fetchProfile = async () => {
    if (!user) return;
    if (user.email === 'alex.vance@example.com') {
      setPatient(MOCK_PATIENT);
      return;
    }
    try {
      const profile = await patientService.getProfile();
      if (profile.patient && profile.patient.id !== 'pat_alex_vance_001') {
        setPatient(profile.patient);
      }
    } catch {
      // Keep clean state
    }
  };

  useEffect(() => {
    if (user) {
      if (user.email === 'alex.vance@example.com') {
        setPatient(MOCK_PATIENT);
      } else {
        setPatient(createCleanPatient(user.id));
        fetchProfile();
      }
    } else {
      setPatient(createCleanPatient());
    }
  }, [user]);

  const updatePatient = async (updated: Partial<Patient>) => {
    setPatient((prev) => ({ ...prev, ...updated }));
    try {
      await patientService.updatePatient(updated);
    } catch {
      // Ignore
    }
  };

  return (
    <UserContext.Provider value={{ patient, updatePatient, refreshProfile: fetchProfile }}>
      {children}
    </UserContext.Provider>
  );
};

export const useUser = (): UserContextType => {
  const context = useContext(UserContext);
  if (!context) {
    throw new Error('useUser must be used within a UserProvider');
  }
  return context;
};
